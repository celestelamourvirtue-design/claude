# pexels-video

Builds a finished video from Pexels-licensed photos and stock clips. You write a
storyboard as JSON; the script searches Pexels, downloads one asset per scene,
and assembles them with ffmpeg — Ken Burns motion on stills, aspect-correct
framing on clips, cross-fades between scenes, optional captions and music.

## Requirements

```sh
apt-get install ffmpeg      # needs ffmpeg + ffprobe
pip install requests
```

## Use

```sh
export PEXELS_API_KEY=...          # free key: https://www.pexels.com/api/
python3 pexels_video.py storyboard.example.json -o out/reel.mp4
```

Two flags worth knowing:

- `--dry-run` resolves every scene and prints which asset it picked, without
  downloading or rendering. One API call per scene, so it is a cheap way to
  audition queries before committing to a render.
- `--selftest` renders a three-scene video from synthetic footage with no
  network access at all, then probes the result. Use it to confirm ffmpeg is
  wired up correctly before blaming a storyboard.

Downloads and per-scene intermediates land in `.cache/` and are reused, so
re-running after a text or timing tweak only re-renders, it does not re-fetch.

## Storyboard

```json
{
  "title": "Morning Routine — 9:16 short",
  "aspect": "9:16",
  "fps": 30,
  "transition": 0.5,
  "audio": null,
  "scenes": [
    { "query": "sunrise over misty mountains", "media": "video", "duration": 3.5,
      "text": "Start before the world does" },
    { "query": "open notebook on wooden desk", "media": "photo", "duration": 3.0,
      "motion": "zoom_in", "text": "Three lines, no more" }
  ]
}
```

### Top level

| Key | Default | Notes |
| --- | --- | --- |
| `title` | `untitled` | Used in the credits file |
| `aspect` | `9:16` | `9:16` (1080×1920), `16:9`, `1:1`, `4:5` |
| `fps` | `30` | |
| `transition` | `0.5` | Cross-fade seconds. `0` cuts straight. Must be shorter than the shortest scene |
| `audio` | `null` | Path to a local music file. Pexels supplies no audio — bring your own |
| `audio_gain_db` | `0` | Applied before the 1s fade-in / 1.5s fade-out |
| `font` | DejaVu Sans Bold | Any `.ttf` |
| `text_size_ratio` | `0.055` | Caption height as a fraction of frame height |

### Per scene

| Key | Default | Notes |
| --- | --- | --- |
| `query` | required | Pexels search terms |
| `media` | `photo` | `photo` or `video` |
| `duration` | `3.5` | Seconds on screen |
| `text` | none | Caption, auto-wrapped, fades in and out |
| `motion` | `zoom_in` | Stills only: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`, `none` |
| `pick` | `0` | Take the nth search result. Bump it to swap a shot you don't like |
| `asset_id` | none | Pin an exact Pexels asset and ignore `query` |
| `clip_start` | `0` | Seconds into the source clip (video scenes) |
| `orientation` | from `aspect` | Override the search orientation filter |

Total runtime is `sum(durations) − transition × (scenes − 1)`, since each
cross-fade overlaps its two neighbours.

## Picking shots

`query` goes straight to Pexels search, so the result is only as good as the
phrase. Concrete beats abstract — "person running on empty road at dawn" returns
usable footage where "motivation" returns stock-photo clichés.

When a query returns something wrong, you have two escapes. `pick` walks down
the result list without changing the query. `asset_id` pins one specific asset
forever, which is what you want once a cut is approved and you need the render
to be reproducible.

## Licensing

Everything comes from Pexels under the [Pexels License](https://www.pexels.com/license/):
free for commercial and personal use, no attribution required, no sign-off
needed from the photographer.

The limits that do apply: you cannot sell unaltered copies of the assets
themselves, you cannot imply that a depicted person or brand endorses your
product, and you cannot use identifiable people in a way that is offensive or
defamatory. Advertising rendered from these assets is fine; reselling them as
a stock pack is not.

Every render writes `ATTRIBUTION.md` and `credits.json` next to the output with
the creator and source URL for each asset. Attribution is not required, but the
list is worth keeping — some ad platforms ask for asset provenance, and it makes
a shot easy to re-license or re-find later.

## Notes

Ken Burns runs on a canvas four times the output size and is scaled back down.
`zoompan` positions its window on whole input pixels, so panning an image at
frame size steps visibly; at 4× each step lands on a quarter-pixel and reads as
smooth. It costs render time and is the reason stills take longer than clips.

The API key is read from the environment only. It is never written to disk,
baked into a storyboard, or embedded in the output.

Free-tier Pexels allows 200 requests/hour. The script makes one search call per
scene, plus one download per asset, and backs off on `429` using `Retry-After`.
