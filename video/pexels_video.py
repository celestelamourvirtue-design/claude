#!/usr/bin/env python3
"""Build a video from Pexels-licensed photos and video clips.

Reads a storyboard (JSON), fetches one asset per scene from the Pexels API,
and assembles them with ffmpeg: Ken Burns motion on stills, aspect-correct
framing on clips, cross-fades between scenes, optional captions and music.

The API key is read from the PEXELS_API_KEY environment variable. It is never
written to disk or into the output.

Usage:
    export PEXELS_API_KEY=...
    python3 pexels_video.py storyboard.json -o reel.mp4

    python3 pexels_video.py storyboard.json --dry-run   # show picks, fetch nothing
    python3 pexels_video.py --selftest                  # render path check, no network
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

import requests

API_ROOT = "https://api.pexels.com"
USER_AGENT = "pexels-video/1.0"

# Ken Burns moves. Anything else in a storyboard is a hard error rather than a
# silent fallback -- a typo'd motion should not quietly render as a static shot.
MOTIONS = ("zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "none")

ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


class PexelsError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Storyboard
# --------------------------------------------------------------------------- #


@dataclass
class Scene:
    query: str
    media: str = "photo"  # "photo" | "video"
    duration: float = 3.5
    text: str | None = None
    motion: str = "zoom_in"  # stills only
    pick: int = 0  # nth search result -- bump to swap the shot
    asset_id: int | None = None  # pin an exact Pexels asset, ignores query
    clip_start: float = 0.0  # seconds into the source clip
    orientation: str | None = None  # portrait | landscape | square

    def __post_init__(self) -> None:
        if self.media not in ("photo", "video"):
            raise ValueError(f"scene media must be 'photo' or 'video', got {self.media!r}")
        if self.motion not in MOTIONS:
            raise ValueError(f"unknown motion {self.motion!r}; pick one of {', '.join(MOTIONS)}")
        if self.duration <= 0:
            raise ValueError(f"scene duration must be positive, got {self.duration}")


@dataclass
class Storyboard:
    scenes: list[Scene]
    title: str = "untitled"
    aspect: str = "9:16"
    fps: int = 30
    transition: float = 0.5  # cross-fade seconds; 0 disables
    audio: str | None = None
    audio_gain_db: float = 0.0
    font: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    text_size_ratio: float = 0.055  # caption height as a fraction of frame height
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self) -> None:
        if self.aspect not in ASPECTS:
            raise ValueError(f"unknown aspect {self.aspect!r}; pick one of {', '.join(ASPECTS)}")
        self.width, self.height = ASPECTS[self.aspect]
        if not self.scenes:
            raise ValueError("storyboard has no scenes")
        # A cross-fade eats from both neighbours, so it cannot exceed the
        # shortest scene or ffmpeg produces a negative xfade offset.
        shortest = min(s.duration for s in self.scenes)
        if self.transition >= shortest:
            raise ValueError(
                f"transition ({self.transition}s) must be shorter than the shortest "
                f"scene ({shortest}s)"
            )

    @property
    def default_orientation(self) -> str:
        w, h = self.width, self.height
        return "portrait" if h > w else ("landscape" if w > h else "square")

    @classmethod
    def load(cls, path: Path) -> "Storyboard":
        raw = json.loads(path.read_text())
        scenes = [Scene(**s) for s in raw.pop("scenes", [])]
        unknown = set(raw) - {f for f in cls.__dataclass_fields__ if f not in ("width", "height")}
        if unknown:
            raise ValueError(f"unknown storyboard keys: {', '.join(sorted(unknown))}")
        return cls(scenes=scenes, **raw)

    def total_duration(self) -> float:
        return sum(s.duration for s in self.scenes) - self.transition * (len(self.scenes) - 1)


# --------------------------------------------------------------------------- #
# Pexels API
# --------------------------------------------------------------------------- #


class PexelsClient:
    """Minimal Pexels client. Honours Retry-After on 429."""

    def __init__(self, api_key: str, *, timeout: int = 30) -> None:
        if not api_key:
            raise PexelsError(
                "PEXELS_API_KEY is not set. Get a free key at https://www.pexels.com/api/ "
                "and export it: export PEXELS_API_KEY=..."
            )
        self.session = requests.Session()
        self.session.headers.update({"Authorization": api_key, "User-Agent": USER_AGENT})
        self.timeout = timeout
        self.remaining: str | None = None

    def _get(self, path: str, params: dict | None = None, *, attempts: int = 4) -> dict:
        url = f"{API_ROOT}{path}"
        for attempt in range(attempts):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt == attempts - 1:
                    raise PexelsError(f"GET {url} failed: {exc}") from exc
                time.sleep(2**attempt)
                continue

            self.remaining = r.headers.get("X-Ratelimit-Remaining", self.remaining)

            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 2**attempt))
                if attempt == attempts - 1:
                    raise PexelsError(
                        "Pexels rate limit hit (free tier is 200 requests/hour). "
                        f"Retry-After: {wait}s"
                    )
                time.sleep(wait)
                continue
            if r.status_code in (401, 403):
                raise PexelsError(
                    f"Pexels rejected the API key ({r.status_code}). "
                    "Check PEXELS_API_KEY is a current key from https://www.pexels.com/api/"
                )
            if not r.ok:
                raise PexelsError(f"GET {url} -> HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        raise PexelsError(f"GET {url} exhausted {attempts} attempts")

    def search_photos(self, query: str, orientation: str, per_page: int) -> list[dict]:
        params = {"query": query, "per_page": per_page, "orientation": orientation}
        return self._get("/v1/search", params).get("photos", [])

    def search_videos(self, query: str, orientation: str, per_page: int) -> list[dict]:
        params = {"query": query, "per_page": per_page, "orientation": orientation}
        return self._get("/videos/search", params).get("videos", [])

    def photo(self, asset_id: int) -> dict:
        return self._get(f"/v1/photos/{asset_id}")

    def video(self, asset_id: int) -> dict:
        return self._get(f"/videos/videos/{asset_id}")

    def download(self, url: str, dest: Path) -> Path:
        if dest.exists() and dest.stat().st_size > 0:
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with self.session.get(url, stream=True, timeout=self.timeout) as r:
            if not r.ok:
                raise PexelsError(f"download {url} -> HTTP {r.status_code}")
            with tmp.open("wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
        tmp.replace(dest)
        return dest


def pick_photo_src(photo: dict) -> str:
    """Largest available rendition -- stills get upscaled for Ken Burns."""
    src = photo.get("src", {})
    for key in ("original", "large2x", "large", "medium"):
        if src.get(key):
            return src[key]
    raise PexelsError(f"photo {photo.get('id')} has no usable src")


def pick_video_file(video: dict, width: int, height: int) -> dict:
    """Smallest rendition that still covers the target frame.

    Downloading a 4K master to render a 1080-wide reel wastes bandwidth and
    encode time, so prefer the smallest file that meets or beats the target on
    both axes; fall back to the largest available if none does.
    """
    files = [f for f in video.get("video_files", []) if f.get("link") and f.get("file_type") == "video/mp4"]
    if not files:
        raise PexelsError(f"video {video.get('id')} has no mp4 rendition")

    def area(f: dict) -> int:
        return (f.get("width") or 0) * (f.get("height") or 0)

    covering = [f for f in files if (f.get("width") or 0) >= width and (f.get("height") or 0) >= height]
    return min(covering, key=area) if covering else max(files, key=area)


# --------------------------------------------------------------------------- #
# ffmpeg
# --------------------------------------------------------------------------- #


def run(cmd: list[str], *, label: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-15:])
        raise RuntimeError(f"{label} failed (exit {proc.returncode}):\n{tail}")


def escape_drawtext(text: str) -> str:
    """Escape for ffmpeg drawtext, which parses : \\ ' and % in its own layer."""
    out = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")
    return out.replace(",", "\\,")


def caption_filter(text: str, sb: Storyboard, duration: float) -> str:
    size = max(18, int(sb.height * sb.text_size_ratio))
    # Wrap by character count rather than pixels: close enough for one or two
    # lines of caption, and avoids a font-metrics dependency.
    lines = textwrap.wrap(text, width=max(14, int(sb.width / (size * 0.55))))
    body = escape_drawtext("\n".join(lines))
    fade = min(0.4, duration / 4)
    alpha = (
        f"if(lt(t,{fade:.3f}),t/{fade:.3f},"
        f"if(lt(t,{duration - fade:.3f}),1,max(0,({duration:.3f}-t)/{fade:.3f})))"
    )
    return (
        f"drawtext=fontfile='{sb.font}':text='{body}':"
        f"fontsize={size}:fontcolor=white:line_spacing={int(size * 0.3)}:"
        f"box=1:boxcolor=black@0.42:boxborderw={int(size * 0.45)}:"
        f"x=(w-text_w)/2:y=h-text_h-{int(sb.height * 0.14)}:"
        f"alpha='{alpha}'"
    )


def photo_scene_filter(scene: Scene, sb: Storyboard) -> str:
    """Cover-crop the still, upscale, then Ken Burns it down to frame size.

    zoompan positions its window on integer input pixels, so panning a
    frame-sized image steps visibly. Rendering the move on a 4x canvas puts
    each step at a quarter-pixel once scaled down, which reads as smooth.
    """
    frames = max(2, int(round(scene.duration * sb.fps)))
    cw, ch = sb.width * 4, sb.height * 4
    zoom_max, pan_zoom = 1.28, 1.14
    last = frames - 1

    if scene.motion == "zoom_in":
        z = f"min(1+({zoom_max - 1:.4f}*on/{last}),{zoom_max})"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif scene.motion == "zoom_out":
        z = f"max({zoom_max}-({zoom_max - 1:.4f}*on/{last}),1)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif scene.motion in ("pan_left", "pan_right"):
        z = str(pan_zoom)
        travel = f"(iw-iw/zoom)*on/{last}"
        x = travel if scene.motion == "pan_right" else f"(iw-iw/zoom)-{travel}"
        y = "ih/2-(ih/zoom/2)"
    elif scene.motion in ("pan_up", "pan_down"):
        z = str(pan_zoom)
        travel = f"(ih-ih/zoom)*on/{last}"
        y = travel if scene.motion == "pan_down" else f"(ih-ih/zoom)-{travel}"
        x = "iw/2-(iw/zoom/2)"
    else:  # none -- still frame, but keep the same graph shape
        z, x, y = "1", "0", "0"

    chain = [
        f"scale={cw}:{ch}:force_original_aspect_ratio=increase",
        f"crop={cw}:{ch}",
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={sb.width}x{sb.height}:fps={sb.fps}",
    ]
    if scene.text:
        chain.append(caption_filter(scene.text, sb, scene.duration))
    chain += ["setsar=1", "format=yuv420p"]
    return ",".join(chain)


def video_scene_filter(scene: Scene, sb: Storyboard) -> str:
    chain = [
        f"scale={sb.width}:{sb.height}:force_original_aspect_ratio=increase",
        f"crop={sb.width}:{sb.height}",
        f"fps={sb.fps}",
    ]
    if scene.text:
        chain.append(caption_filter(scene.text, sb, scene.duration))
    chain += ["setsar=1", "format=yuv420p"]
    return ",".join(chain)


def render_scene(scene: Scene, sb: Storyboard, source: Path, dest: Path) -> Path:
    """Normalise one scene to an intermediate clip.

    Every intermediate shares resolution, fps, SAR and pixel format so the
    xfade chain in assemble() has nothing left to reconcile.
    """
    common = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an"]
    if scene.media == "photo":
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(source),
            "-vf", photo_scene_filter(scene, sb),
            "-frames:v", str(max(2, int(round(scene.duration * sb.fps)))),
            "-r", str(sb.fps), *common, str(dest),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{scene.clip_start:.3f}", "-t", f"{scene.duration:.3f}",
            "-i", str(source),
            "-vf", video_scene_filter(scene, sb),
            "-r", str(sb.fps), *common, str(dest),
        ]
    run(cmd, label=f"scene render ({scene.query!r})")
    return dest


def assemble(clips: list[Path], sb: Storyboard, out: Path) -> None:
    """Chain the intermediates with cross-fades and lay audio underneath."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for clip in clips:
        cmd += ["-i", str(clip)]

    have_music = bool(sb.audio)
    if have_music:
        cmd += ["-i", str(sb.audio)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    audio_idx = len(clips)

    parts: list[str] = []
    if len(clips) == 1 or sb.transition <= 0:
        streams = "".join(f"[{i}:v]" for i in range(len(clips)))
        parts.append(f"{streams}concat=n={len(clips)}:v=1:a=0[v]")
    else:
        durations = [s.duration for s in sb.scenes]
        prev = "[0:v]"
        for i in range(1, len(clips)):
            # Fade i starts one transition before the material already on the
            # timeline runs out. That material is sum(durations[:i]) shortened
            # by one transition for each of the i-1 fades already applied, so
            # the offset reduces to sum(durations[:i]) - i*transition.
            offset = sum(durations[:i]) - sb.transition * i
            label = "[v]" if i == len(clips) - 1 else f"[x{i}]"
            parts.append(
                f"{prev}[{i}:v]xfade=transition=fade:"
                f"duration={sb.transition}:offset={offset:.3f}{label}"
            )
            prev = label

    total = sb.total_duration()
    afilters = [f"atrim=0:{total:.3f}", "asetpts=PTS-STARTPTS"]
    if have_music:
        if sb.audio_gain_db:
            afilters.append(f"volume={sb.audio_gain_db}dB")
        afilters.append(f"afade=t=in:st=0:d=1.0")
        afilters.append(f"afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5")
    afilters.append("aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo")
    parts.append(f"[{audio_idx}:a]{','.join(afilters)}[a]")

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", str(out),
    ]
    run(cmd, label="assemble")


# --------------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------------- #


def write_credits(assets: list[dict], sb: Storyboard, out_dir: Path) -> Path:
    (out_dir / "credits.json").write_text(json.dumps(assets, indent=2) + "\n")
    lines = [
        f"# Credits -- {sb.title}",
        "",
        "All media sourced from Pexels under the [Pexels License]"
        "(https://www.pexels.com/license/): free for commercial and personal use,",
        "no attribution required. Credits are listed here anyway as good practice,",
        "and because some platforms ask for a source list.",
        "",
        "| # | Type | Creator | Source |",
        "| --- | --- | --- | --- |",
    ]
    for i, a in enumerate(assets, 1):
        lines.append(f"| {i} | {a['media']} | [{a['creator']}]({a['creator_url']}) | [Pexels #{a['id']}]({a['url']}) |")
    lines += [
        "",
        "## License limits worth knowing",
        "",
        "- Do not sell unaltered copies of the assets themselves.",
        "- Do not imply the depicted people or brands endorse anything.",
        "- Do not use identifiable people in a way that is offensive or defamatory.",
        "",
    ]
    dest = out_dir / "ATTRIBUTION.md"
    dest.write_text("\n".join(lines))
    return dest


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


def resolve_scene(client: PexelsClient, scene: Scene, sb: Storyboard) -> dict:
    """Search (or fetch by id) and return normalised asset metadata."""
    orientation = scene.orientation or sb.default_orientation

    if scene.media == "photo":
        if scene.asset_id:
            hit = client.photo(scene.asset_id)
        else:
            results = client.search_photos(scene.query, orientation, per_page=max(1, scene.pick + 1))
            if len(results) <= scene.pick:
                raise PexelsError(
                    f"query {scene.query!r} returned {len(results)} photo(s); "
                    f"pick={scene.pick} is out of range"
                )
            hit = results[scene.pick]
        return {
            "id": hit["id"],
            "media": "photo",
            "creator": hit.get("photographer", "unknown"),
            "creator_url": hit.get("photographer_url", "https://www.pexels.com"),
            "url": hit.get("url", ""),
            "download": pick_photo_src(hit),
            "ext": ".jpg",
        }

    if scene.asset_id:
        hit = client.video(scene.asset_id)
    else:
        results = client.search_videos(scene.query, orientation, per_page=max(1, scene.pick + 1))
        if len(results) <= scene.pick:
            raise PexelsError(
                f"query {scene.query!r} returned {len(results)} video(s); "
                f"pick={scene.pick} is out of range"
            )
        hit = results[scene.pick]

    src_duration = hit.get("duration") or 0
    if src_duration and scene.clip_start + scene.duration > src_duration:
        raise PexelsError(
            f"video {hit['id']} is {src_duration}s; clip_start={scene.clip_start} + "
            f"duration={scene.duration} overruns it"
        )
    chosen = pick_video_file(hit, sb.width, sb.height)
    user = hit.get("user", {})
    return {
        "id": hit["id"],
        "media": "video",
        "creator": user.get("name", "unknown"),
        "creator_url": user.get("url", "https://www.pexels.com"),
        "url": hit.get("url", ""),
        "download": chosen["link"],
        "ext": ".mp4",
        "source_resolution": f"{chosen.get('width')}x{chosen.get('height')}",
    }


def build(sb: Storyboard, out: Path, work: Path, *, dry_run: bool) -> None:
    client = PexelsClient(os.environ.get("PEXELS_API_KEY", ""))
    cache, scenes_dir = work / "assets", work / "scenes"
    cache.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(parents=True, exist_ok=True)

    print(f"» {sb.title}  [{sb.aspect} {sb.width}x{sb.height} @ {sb.fps}fps, "
          f"{len(sb.scenes)} scenes, {sb.total_duration():.1f}s]\n")

    assets = []
    for i, scene in enumerate(sb.scenes, 1):
        asset = resolve_scene(client, scene, sb)
        assets.append(asset)
        extra = asset.get("source_resolution", "")
        print(f"  {i:2}. {scene.media:5} {scene.query!r} -> #{asset['id']} "
              f"by {asset['creator']} {extra}")

    if dry_run:
        print(f"\n-- dry run, nothing downloaded. Rate limit remaining: {client.remaining}")
        return

    print()
    clips = []
    for i, (scene, asset) in enumerate(zip(sb.scenes, assets), 1):
        src = client.download(asset["download"], cache / f"{asset['id']}{asset['ext']}")
        dest = render_scene(scene, sb, src, scenes_dir / f"scene{i:02}.mp4")
        clips.append(dest)
        print(f"  rendered scene {i}/{len(sb.scenes)}")

    out.parent.mkdir(parents=True, exist_ok=True)
    assemble(clips, sb, out)
    credits = write_credits(assets, sb, out.parent)

    size_mb = out.stat().st_size / 1e6
    print(f"\n✓ {out}  ({size_mb:.1f} MB, {sb.total_duration():.1f}s)")
    print(f"✓ {credits}")


# --------------------------------------------------------------------------- #
# Selftest -- exercises the render path with locally generated media
# --------------------------------------------------------------------------- #


def selftest(work: Path, out: Path) -> None:
    """Render a video end to end without touching the network.

    Uses ffmpeg's synthetic sources in place of Pexels downloads so the
    filtergraph, cross-fade offsets, captions and muxing are all exercised.
    """
    work.mkdir(parents=True, exist_ok=True)
    stills, clip = work / "still", work / "clip.mp4"
    stills.mkdir(exist_ok=True)

    for i, src in enumerate(
        ["gradients=s=1500x2400:n=3", "testsrc2=s=1500x2400", "cellauto=s=1500x2400"], 1
    ):
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", src, "-frames:v", "1", str(stills / f"{i}.png")], label="selftest still")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
         "-i", "smptebars=s=1920x1080:r=30", "-t", "6", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(clip)], label="selftest clip")

    sb = Storyboard(
        title="selftest",
        scenes=[
            Scene(query="a", media="photo", duration=3.0, motion="zoom_in", text="Ken Burns: zoom"),
            Scene(query="b", media="video", duration=3.0, text="Clip: cover-cropped"),
            Scene(query="c", media="photo", duration=3.0, motion="pan_right", text="Ken Burns: pan"),
        ],
    )
    sources = [stills / "1.png", clip, stills / "3.png"]
    clips = [
        render_scene(s, sb, src, work / f"scene{i}.mp4")
        for i, (s, src) in enumerate(zip(sb.scenes, sources), 1)
    ]
    assemble(clips, sb, out)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_name,width,height,r_frame_rate",
         "-of", "json", str(out)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(probe.stdout)
    dur = float(info["format"]["duration"])
    expected = sb.total_duration()
    v = next(s for s in info["streams"] if s.get("width"))
    a = next((s for s in info["streams"] if not s.get("width")), None)

    print(f"  output      : {out}")
    print(f"  video       : {v['codec_name']} {v['width']}x{v['height']} @ {v['r_frame_rate']}")
    print(f"  audio       : {a['codec_name'] if a else 'MISSING'}")
    print(f"  duration    : {dur:.2f}s (expected {expected:.2f}s)")

    problems = []
    if abs(dur - expected) > 0.35:
        problems.append(f"duration off by {abs(dur - expected):.2f}s")
    if (v["width"], v["height"]) != (sb.width, sb.height):
        problems.append("resolution mismatch")
    if not a:
        problems.append("no audio stream")
    if problems:
        raise SystemExit("selftest FAILED: " + "; ".join(problems))
    print("\n✓ selftest passed -- render path is working end to end")


# --------------------------------------------------------------------------- #


def main() -> int:
    p = argparse.ArgumentParser(
        description="Build a video from Pexels-licensed photos and clips.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("storyboard", nargs="?", type=Path, help="storyboard JSON")
    p.add_argument("-o", "--out", type=Path, default=Path("out/reel.mp4"))
    p.add_argument("-w", "--work", type=Path, default=Path(".cache"),
                   help="scratch dir for downloads and intermediates (default: .cache)")
    p.add_argument("--dry-run", action="store_true", help="resolve scenes, download nothing")
    p.add_argument("--selftest", action="store_true", help="verify the render path offline")
    args = p.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("error: ffmpeg and ffprobe are required (apt-get install ffmpeg)", file=sys.stderr)
        return 1

    try:
        if args.selftest:
            selftest(args.work / "selftest", args.out)
            return 0
        if not args.storyboard:
            p.error("a storyboard is required unless --selftest is given")
        build(Storyboard.load(args.storyboard), args.out, args.work, dry_run=args.dry_run)
    except (PexelsError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
