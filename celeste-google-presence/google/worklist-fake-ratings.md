# Fabricated star ratings — live on the storefront right now

**Correction.** Earlier in this audit I told you the fake-review problem was
"a landmine, not a live violation." That was wrong, and I want to be precise
about why, because the distinction changes what you do this week.

I checked the wrong metafield namespace. I scanned `reviews.*` and `judgeme.*`,
found them empty on active products, and concluded nothing was rendering. The
fabricated data lives in a third namespace — `air_reviews_product` — which I
had not looked at. It is live.

**Nothing in this file has been executed.**

---

## What is actually rendering

Sampled 20 live, published, active products. **Every single one** carries
fabricated review aggregates:

| Product | `review_avg` | `review_count` |
|---|---:|---:|
| `lamour-ultrasculpt-...-training-leggings` *(flagship)* | 4.8 | **37,118** |
| `celeste-body-shaping-crossover-pocket-leggings-7-8` | 4.7 | 30,076 |
| `celeste-high-waisted-back-side-pocket-denim-casual-leggings` | 4.7 | 26,911 |
| `celeste-high-waisted-drawstring-...-wide-leg-casual-pants` | 4.7 | 21,863 |
| `flex-straight-jean` | 4.8 | 19,697 |
| `celeste-super-high-waisted-...-yoga-shorts` | 4.7 | 19,396 |
| …and 14 more, all 4.3–4.8, counts from 222 to 30,076 | | |

For scale: **Judge.me reports 142 reviews across the entire store**, and the
flagship's own Judge.me badge reads `data-number-of-reviews='0'` — "No reviews".

So one product page claims 37,118 reviews on a store with 142.

## It reaches the page. Here is the exact path.

The live product template (`templates/product.json`) has a `rating` block in
`block_order`, and it is enabled. That block renders
`snippets/gs-buybox-rating.liquid`, which resolves a rating in this order:

```liquid
1. product.metafields.gymshark.star_rating        (scraped Gymshark ratings)
2. product.metafields.reviews.rating              (native — absent on these products)
3. product.metafields.air_reviews_product.review_avg  ← falls through to here
```

Then renders whenever the count is above zero:

```liquid
{%- if rating_value != blank and rating_count_display > 0 -%}
  <span class="gs-rating__value">{{ rating_display }}</span>
  <span class="gs-rating__count">({{ rating_count_display }})</span>
```

Celeste products have no `gymshark.star_rating` and no `reviews.rating`, so the
fallback fires every time. **The buy box on your flagship PDP is displaying
"4.8 (37118)" to every visitor.**

## Someone already spotted this and built the fix — it just is not wired up

`snippets/tc-rating-data.liquid` exists in the same theme and its own
documentation says, verbatim:

> The air_reviews_product.review_avg / review_count metafields are deliberately
> NOT used: on this store they hold figures the app's own summary does not back
> (for example 37,118 reviews against 0 published).

That snippet computes a rating from Air Reviews' *published star buckets*
instead — the real ones, which sum to zero. It is correct. It is simply not
what the buy-box rating block calls.

That is good news: the judgement call has already been made correctly by
whoever wrote `tc-rating-data.liquid`. This is a wiring job, not a debate.

---

## What to do

### 1. Right now — stop it rendering

Two options. Take the first.

**Option A (safest, no code):** Online Store → Themes → Customize → Product
template → remove the **rating** block from the buy box. One click. It stops
displaying immediately and nothing else changes.

**Option B (correct, small code change):** in
`snippets/gs-buybox-rating.liquid`, delete the third fallback — the
`air_reviews_product.review_avg` / `review_count` branch — so the block renders
only from `reviews.rating` or the Gymshark import. Better still, change it to
call `tc-rating-data.liquid`, which already does the right thing.

Do not "fix" this by editing the numbers down to something believable. A
smaller invented number is the same violation.

### 2. Delete the source data

The metafields themselves should go, or they will resurface the next time any
theme or app reads them.

Air Reviews app → the product review data. If the app cannot clear the
aggregates, the metafields can be deleted via the Admin API
(`metafieldsDelete` on `air_reviews_product.review_avg` and `review_count`).
Ask me and I will stage that mutation for review — I have not run any writes
against your store in this session and will not without you saying so.

Also: Judge.me → Manage Reviews → filter for bodies containing `DEMO` → delete
the 100 rows on product 7830848110643. Those are still the separate, latent
problem I described before, and deleting them is still worth doing.

And check **Judge.me → Settings → Rich snippets** is OFF. Judge.me can emit its
own structured data independently of your theme, which would bypass everything
above.

### 3. Check what else is one toggle away

The product template also contains, currently `"disabled": true`:

- A **`reviews-wall`** section — twice, duplicated — with six invented
  testimonials ("Nadia K., Brooklyn, NY", "Priya M., Austin, TX"), each marked
  `"verified": true`, under the heading **"What 6,412 people said"** and
  `aggregate_rating: 4.9, aggregate_count: 6412`, subtitled *"Verified at
  checkout. Nothing incentivised, nothing edited."*
- A **`comparison-table`** section making competitive claims ("Wear tested to
  200 sessions before release", "Opacity tested at full fold under studio
  lighting") against unnamed competitors.
- A **`fabric-technology`** section asserting "78% recycled nylon, 22%
  elastane" and "Lab tested to 200 wears and washes without loss of
  compression."

They are disabled, so they are not live. Each is one toggle from being live,
and each is written to read as verified fact. Delete the ones you cannot
substantiate rather than leaving them one click away — including the duplicate
`reviews_wall_7eGMyg` section.

The fabric claims may well be true; if they are, keep them and hold the lab
report. If they are placeholder copy, they are a bigger liability than an empty
section.

---

## Why this outranks the SEO work

Everything else in this audit is about how Google perceives you. This one is
about what US law says.

The **FTC Rule on Consumer Reviews and Testimonials (16 CFR Part 465)** took
effect in October 2024. It prohibits creating, selling or disseminating
consumer reviews that misrepresent that they are by an actual purchaser, and it
reaches *review indicators* — star ratings and review counts — not just review
text. It carries civil penalties per violation. VIRTULIFT LLC is a US entity
selling to US consumers.

A displayed "4.8 from 37,118 reviews" on a product with zero reviews is
squarely what that rule addresses.

Separately, Google's review-snippet policies prohibit marked-up ratings that
are not genuine. **You are not currently exposed there** — `meta-tags.liquid`
reads only `reviews.rating`, which is absent, so no `aggregateRating` is being
emitted. That is luck rather than design, and it is why the revised
`meta-tags.liquid` in this PR keeps that guard and documents it.

---

## Sequence

This goes to the top, above the Gymshark products. The Gymshark problem costs
you a brand entity. This one carries legal exposure, and the fix is a single
click in the theme customiser.

1. **This file, step 1** — stop the rating block rendering. Today.
2. `worklist-competitor-products.md` — the 170 Gymshark products.
3. `worklist-collections-sitelinks.md`
4. `worklist-blog-cleanup.md`
5. `../shopify/store-identity-values.md`
6. `google-tools-setup.md`
