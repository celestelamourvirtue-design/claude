# Fabricated review data — a loaded gun, not a fired one

**This file has been corrected twice. Read the correction; it is the useful part.**

- **First version:** I said the fake-review problem was "latent, not live." I had
  checked the `reviews.*` and `judgeme.*` metafield namespaces and missed a
  third, `air_reviews_product`.
- **Second version:** I found that third namespace, found a theme snippet that
  reads it, and rewrote this file to say fabricated ratings were **rendering
  live on your flagship product**. I said that emphatically.
- **That was wrong too.** Adversarial verification of my own finding challenged
  the render path, and on tracing it properly the challenge was right.

Here is what is actually true.

**Nothing in this file has been executed.**

---

## What is true

**The fabricated data exists.** Of the active catalogue, roughly 178 products
carry `air_reviews_product.review_avg` and `review_count` metafields with
invented values. Verified examples:

| Product | `review_avg` | `review_count` |
|---|---:|---:|
| `lamour-ultrasculpt-...-training-leggings` *(flagship)* | 4.8 | 37,118 |
| `celeste-high-waisted-button-...-casual-pants` | 4.7 | 53,632 |
| `celeste-body-shaping-crossover-pocket-leggings-7-8` | 4.7 | 30,076 |
| `celeste-mid-rise-drawstring-...-joggers` | 4.6 | 25,670 |

The flagship's own `air_reviews_product.data` metafield holds `{"reviews":[]}`
with all five star buckets at zero. The app's own summary does not back its own
headline number. Judge.me, separately, reports 142 reviews store-wide.

**Nothing renders it.** This is the part I got wrong, and the trace matters:

- `sections/main-product.liquid` line 160 handles the `rating` block, and it
  renders **`snippets/rating.liquid`** — passing `block.settings.manual_rating`
  and `manual_count`, both of which are blank on the live product template.
- `snippets/rating.liquid` reads **only** `product.metafields.reviews.rating`
  and `reviews.rating_count`. It contains no reference to `air_reviews`. It is
  gated `{%- if rating and settings.reviews_source != 'off' -%}`, so a nil
  rating emits nothing at all — not even an empty widget.
- Active products have **no `reviews.rating` metafield** (verified across 50).
- `config/settings_data.json` has `reviews_source = 'metafield'` and
  `reviews_fallback_count = ''`.
- There is **no Air Reviews app embed** in the live theme.
- `meta-tags.liquid` sources `aggregateRating` from `reviews.rating`, which is
  null — so no rating reaches the JSON-LD either.

**My error was specific and worth naming.** I searched the theme by filename,
found `snippets/gs-buybox-rating.liquid` — which *does* read
`air_reviews_product.review_avg` as a third fallback — and assumed it was what
the enabled `rating` block renders. It is not. `gs-buybox-rating.liquid` is
referenced **nowhere** in `main-product.liquid`; it is an orphan left over from
an earlier "GS buybox" build. I inferred a render path from a filename instead
of reading the 137 KB section file that would have settled it.

So: no shopper sees 4.8 / 37,118. No crawler sees it. Nothing is being
disseminated.

## What this means for priority

**This is not Phase 0 and the Gymshark products go back to number one.**

It is the same category as the Judge.me DEMO rows: fabricated data sitting in
the store with no current render path, one wiring change away from being real.
That is worth cleaning up deliberately, not worth dropping everything for.

What would make it fire:

- Someone wires the `rating` block to `gs-buybox-rating.liquid` instead of
  `rating.liquid` — a plausible thing to do, since the orphan snippet is
  *named* like the buy-box renderer and was clearly built for it.
- Any review app writes `reviews.rating` from the Air Reviews figures.
- Judge.me's own rich-snippet feature is switched on.
- The Air Reviews app embed is added back to the theme.

## What to do — deliberately, not urgently

### 1. Delete the fabricated metafields

Remove `air_reviews_product.review_avg` and `review_count` from the ~178
products carrying them. Either through the Air Reviews app, or via
`metafieldsDelete` on the Admin API. **I have run no writes against your store
in this session and will not without you asking** — say the word and I will
stage that mutation for review.

### 2. Delete the orphan snippet

Remove `snippets/gs-buybox-rating.liquid` from the theme, or strip its
`air_reviews_product` fallback. Leaving a snippet that reads fabricated data,
named as though it belongs in the buy box, is the trap that fires this.

### 3. Delete the Judge.me DEMO rows

Judge.me → Manage Reviews → filter for bodies containing `DEMO` → delete the
100 rows on product 7830848110643. Bodies read *"DEMO / TEST REVIEW — NOT FOR
PUBLICATION. Layout test scenario 100…"* under reviewers named "DEMO S.B.".
Delete rather than unpublish.

### 4. Confirm Judge.me rich snippets are OFF

Judge.me → Settings → Rich snippets. It can emit structured data independently
of your theme, bypassing every guard above.

### 5. Deal with the disabled template sections

`templates/product.json` contains, at `"disabled": true`:

- **Two duplicate `reviews-wall` sections** with six invented testimonials
  ("Nadia K., Brooklyn, NY", "Priya M., Austin, TX"), each marked
  `"verified": true`, headed **"What 6,412 people said"** with
  `aggregate_rating: 4.9, aggregate_count: 6412`, subtitled *"Verified at
  checkout. Nothing incentivised, nothing edited."*
- A **`comparison-table`** asserting "Wear tested to 200 sessions before
  release" and "Opacity tested at full fold under studio lighting".
- A **`fabric-technology`** section asserting "78% recycled nylon, 22%
  elastane" and "Lab tested to 200 wears and washes without loss of
  compression."

These are genuinely one click from live, and every one is written to read as
verified fact. Delete what you cannot substantiate. If the fabric claims are
true, keep them and hold the test report.

## On the legal framing — also corrected

My previous version said this was live FTC exposure under 16 CFR Part 465 with
eight-figure penalties. Two problems with that, both fair hits:

1. **The rule turns on dissemination.** 16 CFR 465.2 reaches a business that
   writes, creates, sells, purchases or *disseminates* a fake review. Values
   sitting in a metafield with no render path are not disseminated. No
   violation is accruing.
2. **I could not verify the rule text or the penalty figure from here** —
   ecfr.gov is blocked by this environment's egress policy. And Part 465
   governs consumer *reviews and testimonials*, meaning submitted evaluations;
   a bare fabricated aggregate with no underlying reviews is a cleaner FTC Act
   Section 5 / Endorsement Guides theory than a clean 465 hit.

So: cleaning this up is the right call, on ordinary "don't keep fake numbers in
your database" grounds and because the trap is easy to spring. It is not a fire
and I should not have called it one. If you want a defensible read on the
liability, that is a question for a lawyer with the actual rule text in front
of them, not for an audit that cannot reach ecfr.gov.

---

## Where this sits

1. `worklist-competitor-products.md` — the 170 Gymshark products. **Start here.**
2. `worklist-collections-sitelinks.md`
3. **This file** — clean the fabricated data before anything can wire it up
4. `worklist-blog-cleanup.md`
5. `../shopify/store-identity-values.md`
6. `google-tools-setup.md`
