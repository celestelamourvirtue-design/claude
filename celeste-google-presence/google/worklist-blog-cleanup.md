# Blog cleanup worklist — the single highest-priority item

**Status: nothing here has been executed. This is a list, not an action.**

Pulled from the Shopify Admin API on 2026-09-24. Blog `News`, handle
`verbs-list`, `gid://shopify/Blog/89583812659`. Full enumeration, both pages,
57 of 57 articles accounted for.

---

## What is actually there

| Group | Count | Published? |
|---|---:|---|
| Scraped third-party articles, unrelated to activewear | 45 | Yes, all of them |
| App test artifact (`pagefly blog`) | 1 | Yes |
| On-topic shapewear articles | 2 | Yes |
| On-topic shapewear articles | 9 | No (draft) |
| **Total** | **57** | |

**46 publicly indexable pages on celestelamour.com are not about this business.**

The blog's own handle is `verbs-list` — it is named after the article
"229 Common English Verbs With Examples · PrepScholar", which means even the
blog's URL, `celestelamour.com/blogs/verbs-list/`, is an artifact of the
scraping tool rather than a decision anyone made.

## Why this outranks every other fix

The other findings in this audit are optimisation. This one is the reason the
brand does not read as legitimate.

Google evaluates quality at the site level, not just page by page, and those
signals feed entity confidence. A domain publishing 45 plagiarised
college-admissions and astrology articles under a byline ("Victoria Lamar")
with keyword-stuffed tags is the textbook fingerprint of a content-farmed
dropshipping site. No amount of Organization schema overrides that, because
schema is a *claim* and site quality is *evidence*. You cannot assert your way
past it.

It is also worse than passive. The theme's `meta-tags.liquid` emits `Article`
JSON-LD on every one of these pages with `"publisher": "Celeste L'Amour"` — the
brand is formally claiming authorship of scraped content, in machine-readable
form, to Google.

And it explains the symptom in the screenshots directly. Google's image block
for "celeste lamour" returns a Brocéliande colouring book, a perfume bottle and
a pair of sandals; its AI Overview returns a Bronx nail salon. Google has no
confident model of what this domain is about, because 46 of its indexable
content pages say it is about SAT scores and star signs.

---

## Delete these 45 — scraped, off-topic, all currently published

```
convert-celsius-to-fahrenheit
hazel-eyes-color
gemini-traits
cool-easy-drawing-ideas
how-many-glasses-in-a-gallon-of-water
capricorn-traits-personality
virgo-traits-personality
the-great-gatsby-american-dream
highest-scoring-college-football-games
cancer-traits-personality
greater-than-sign-less-than-sign
best-colleges
list-of-extracurricular-activities-examples
gemini-compatiblity-signs
sasha-obama-transfers-to-usc
how-many-teaspoons-in-a-tablespoon
penn-state-admission-requirements
how-many-millions-in-a-billion
what-side-is-your-heart-on
camel-spider-size-bite-pictures
persuasive-speech-topics
how-to-get-into-northwestern
lsat-score-range
ap-score-release-dates
romeo-and-juliet-summary
nyu-admission-requirements
best-colleges-in-florida
rainbow-color-order
hbcu-colleges
how-to-convert-your-gpa-to-a-4-0-scale-calculator
how-to-get-into-stanford
best-riddles-for-teens-and-adults
30-60-90-triangle-ratio-formula
libra-traits-personality
cursive-s-capital-lowercase
what-is-a-good-sat-score-a-bad-sat-score-an-excellent-sat-score
disney-trivia-for-kids
yin-yang-symbol
virgo-compatibility-signs
detective-riddles-for-kids
university-of-florida-admission-requirements
how-many-pints-in-a-gallon
how-old-freshman-sophomore-junior-senior-age
race-vs-ethnicity-vs-nationality
verbs-list
```

Apparent sources, from the title suffixes still attached: PrepScholar,
Ivy Coach, College Transitions, Shemmassian Academic Consulting. The suffixes
were never stripped, which is why they are identifiable at a glance — and why
anyone at Google, or any journalist, or any customer who clicks the blog, can
identify them at a glance too.

Separately, these articles are almost certainly being hosted without licence.
Deleting them closes a copyright exposure as well as an SEO one.

## Delete this 1 — app test artifact

```
pagefly-blog
```

## Keep and review these 2 — published, on-topic

```
expert-tips-for-selecting-shapewear-post-surgery
fleece-shapewear-a-winter-fashion-revolution
```

Read both before keeping them. They are topically adjacent, but they came from
the same blog as the other 45, so check whether they are original writing or
spun from somewhere else. If you cannot establish they are original, treat
them like the 45.

Note also that "shapewear post-surgery" is a medical-adjacent claim. If it
stays, it should not imply any clinical benefit.

## Decide on these 9 — unpublished drafts, on-topic

```
upgrade-your-active-wear-with-a-lightweight-bra
seamless-shapewear-perfect-fit-for-every-occasion
double-layer-fabric-the-secret-to-firm-chest-support
breathable-latex-girdle-the-fitness-essential
v-neck-tops-enhance-your-wardrobe-effortlessly
finding-your-fit-bodysuit-shaper-sizing
elevate-outfits-with-ribbed-eco-shapewear-romper
stylish-compression-black-latex-waist-vest-explained
seamless-tank-perfect-for-any-occasion
```

These are drafts, so they are not indexable and pose no current risk. They
read as generic AI-generated filler. Publishing thin content on a domain that
is recovering from a scaled-content problem is the one thing that would make
recovery slower, so leave them unpublished until the cleanup has settled.

---

## How to remove them — the part that matters

Deleting a Shopify article makes its URL return **404**. That works, but it is
the slow path: Google will retry a 404 for a long time before dropping it,
because 404 means "not here right now" and Google treats it as possibly
temporary.

**410 Gone** means "deleted deliberately, stop asking" and is processed
noticeably faster. Shopify does not let you set a 410 on a deleted article
natively, so there are two realistic routes:

1. **Delete, then request removal in Search Console.** Delete all 46 articles,
   then use Search Console → Removals → "Temporarily remove URL" for the
   `/blogs/verbs-list/` prefix. That hides them from results within about a
   day. The removal itself lasts roughly six months, which is ample time for
   the 404s to be processed permanently. This is the route to take — it needs
   no code and no app.

2. **Redirect only where it is honest.** Do *not* 301 these to the homepage or
   to a collection. A mass redirect of 46 unrelated URLs to commercial pages is
   itself a pattern Google treats as manipulative, and irrelevant redirects are
   handled as soft-404s anyway. Redirect only if a genuinely equivalent page
   exists, which here it does not for any of the 45.

**Do not** start by adding `Disallow: /blogs/verbs-list/` to robots.txt. That
blocks crawling, which prevents Google from ever seeing that the pages are
gone, and indexed URLs can persist as bare links with no snippet. Crawling and
indexing are different controls; this is the classic way people make a removal
permanent by accident. There is a longer note on this in
`../theme/templates/robots.txt.liquid`.

## Then check for a manual action

Search Console → Security & Manual Actions → **Manual actions**.

If there is a "Thin content with little or no added value" or "Pure spam"
action listed, deletion alone will not lift it — you must file a
reconsideration request after cleaning up, describing what was removed and
what changed. If the panel says "No issues detected", the effect has been
algorithmic, and it lifts on its own over subsequent recrawls with no request
needed.

Check this before doing anything else, because the answer changes the timeline
you should expect: algorithmic recovery is weeks, a reconsideration request is
weeks *after* review.

## What replaces it

Do not refill the blog to hit a number. Three genuinely useful pieces written
from things this business actually knows — how the scrunch knit is
constructed, how to choose between compressive and easy fit, how the sizing
maps to real body measurements — will do more for the brand entity than fifty
articles ever did. The `/pages/celeste-lamour` "Fabric Engineer Exposes the
Legging Flaw" page suggests that writing already exists in some form.

Also rename the blog. `News` at `/blogs/verbs-list` should become something
like `Journal` at `/blogs/journal`. Changing the handle changes the URL, so do
it at the same time as the deletion rather than afterwards, and let the single
redirect for the blog index be the one redirect you do create.
