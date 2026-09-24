# Collections and navigation — the sitelinks worklist

Pulled from the Shopify Admin API and the live theme's own section JSON on
2026-09-24. Live theme is `gid://shopify/OnlineStoreTheme/145734172723`
("Copy of GS-style PDP build - Used Sep 17 - 20th", role MAIN).

**Status: nothing here has been executed.**

---

## Why this is the file that produces the sitelinks block

Halara's search result shows six sitelinks — Women's Joggers & Pants, Women's
Dresses, Women's Plus Size Clothing, Best-Selling Women's Clothing, Buy 2 Get 1
Free, Leggings for Women. You cannot request those. Google generates them from
a site's own internal link structure: it promotes pages that are clearly
labelled, distinctly titled, substantively different from each other, and
prominently linked from the site itself.

Celeste L'Amour has 90 collections. Here is what Google currently has to work
with.

| Signal | Count | Share |
|---|---:|---:|
| Collections with a `seo.title` set | 10 of 90 | 11% |
| …of which carry **Gymshark's** copy | 9 of 10 | — |
| Collections with any description body | 7 of 90 | 8% |
| Collections with a collection image | 10 of 90 | 11% |
| Collections linked from any sitewide menu or the homepage | 10 of 90 | 11% |
| **Collections with zero internal links** | **80 of 90** | **89%** |

And the homepage — the single most important page for establishing hierarchy —
links to **exactly one collection**. `templates/index.json` has 16 sections;
the only collection reference in the entire file is a `featured-collection`
pointing at `best-sellers`. Ten separate calls-to-action (three hero slides,
four activity tiles, a lookbook frame and its CTA) all point at the **same
single product URL**.

So Google is being shown a site with one category and one product. That is
precisely the shape of site that does not get a sitelinks block.

---

## 1. CRITICAL — Gymshark's copy is being served from celestelamour.com

Nine `gymshark-demo-*` collections are published and carry Gymshark's own title
tags and meta descriptions verbatim. These are the *only* collections on the
store with SEO copy written at all.

Verbatim from the API, `gymshark-demo-leggings-womens` (170 products,
published):

> **seo.title:** `Women's Leggings - For Gym, Workout & Everyday`
> **seo.description:** `Experience new levels of comfort with Gymshark gym leggings for women. Our collection has everything you need from the gym to lounging. FREE DELIVERY available.`

Others include `gymshark-demo-high-waisted-leggings` → "High Waisted Leggings -
Gymshark", `gymshark-demo-ruched-bum` → "Butt Lifting & Scrunch Butt Leggings -
Gymshark", `gymshark-demo-seamless-leggings` → "Seamless Leggings – Famous for
Comfort…".

There is also an unrendered navigation menu named `gymshark-leggings`
containing eight links to `/collections/gymshark-demo-*` plus nine
query-parameter URLs like `?range=vital` and `?activities=lifting` — a copied
menu tree.

**Why it is the worst item on this list for the stated goal.** You are asking
Google to build a brand entity for Celeste L'Amour. The strongest brand signal
currently present on the collection layer is a *different brand's name*, in the
title tag, on pages that outnumber your own SEO'd pages nine to one. It is also
a trademark exposure, not only an SEO one.

**Do:** Collections → filter handle prefix `gymshark-demo`. For all ten: clear
the Page title and Meta description entirely, then unpublish from the Online
Store channel (Publishing → Manage → uncheck Online Store). Delete the
`gymshark-leggings` menu under Online Store → Navigation. Move any product
membership you actually need to your own collections first.

## 2. CRITICAL — Halara's collections and images too

`halara-leggings` (31 products) is published and its description is the
**verbatim duplicate** of `/collections/leggings`, so two published URLs carry
identical body copy.

Three handles contain a raw ™ character, which percent-encodes into ugly URLs:

- `halara-ultrasculpt™-leggings` → `/collections/halara-ultrasculpt%E2%84%A2-leggings`
- `softlyzero™-leggings`
- `ultrasculpt™-training`

"UltraSculpt" and "SoftlyZero" are both Halara product-line names. Five
collection images have filenames ending `-342x.webp`
(`889947166610-342x.webp`, `342238255364-342x.webp`, `3186731635-342x.webp`,
`060937506855-342x.webp`) — that derivative suffix is Halara's CDN naming
convention. A product image elsewhere in the catalogue is stored under a
filename containing `mpir.halarastatic.com`.

**Do:** rename the handles to `sculpt-leggings`, `buttery-soft-leggings`,
`training-leggings` (leave "Create a URL redirect" checked so Shopify writes the
301). Unpublish `halara-leggings` and 301 it to `/collections/leggings`. Replace
every `-342x.webp` image with your own photography.

## 3. CRITICAL — Three published pages are all titled "Leggings"

`leggings` (42 products, real description, no seo.title), `halara-leggings`
(31, identical description), `gymshark-demo-leggings-womens` (170, Gymshark's
seo.title). All three published.

The live footer's `main-menu` links to `halara-leggings` under the anchor text
**"Collection"** and to `gymshark-demo-leggings-womens` under the anchor text
**"Products"**, while the header links to `leggings`. Three URLs, three generic
or conflicting anchors, one topic. Google has to pick one and has been given no
reason to prefer yours.

**Do:** keep `/collections/leggings` only. Unpublish the other two and 301 both
to it.

## 4. CRITICAL — Fix the homepage's internal links

This is the change that most directly creates sitelinks eligibility.

In Online Store → Themes → Customize:

- **Activity tiles** ("Shop by practice"): each of the four tiles currently
  overrides its link to the one product URL. Clear that override and set the
  `collection` field instead — t1 Flow → `yoga-pilates`, t2 Train →
  `running-workout`, t3 Restore → `daily-casual`, t4 Everyday → `leggings`.
- **Hero slides**: point slide CTAs at category pages, not all at one product.
- **Add a collection-list section** above the fold linking the eight candidates
  below, each with anchor text matching its page title.

## 5. HIGH — The sitelinks candidate set

Lock these eight and bring each to eligibility. Handles are real; the state
column is what the API returned.

| # | Handle | Products | Current state |
|---|---|---:|---|
| 1 | `leggings` | 42 | description + image set, `seo` NULL. Flagship. |
| 2 | `joggers` ("Joggers & Pants") | 30 | empty description, `seo` NULL, **not in the header** — the header's "Pants" item points at `daily-casual` instead |
| 3 | `dresses-skirts` | 30 | in header, empty description, `seo` NULL |
| 4 | `shorts` | 31 | in header, empty description, `seo` NULL |
| 5 | `denim` | 30 | in header, empty description, `seo` NULL |
| 6 | `best-sellers` | 199 | **full SEO + description + image — and in no menu at all** |
| 7 | `buy-2-get-1-free` | 82 | empty description, `seo` NULL, zero internal links |
| 8 | `plus-size` | **0** | published with no products |

Two things to notice. `best-sellers` is the one collection that is properly
written — and nothing links to it; the header links to a *different* collection
called `bestsellers` (179 products). And `plus-size` is published while empty,
which is the one Halara sitelink you cannot copy until you actually stock it.

**For each of the eight:** set a Page title on the pattern
`<Category> for Women | Celeste L'Amour` under 60 characters, write 140–155
characters of real meta description naming fabric, fit feature and size range,
write 2–3 sentences of body copy, set a collection image, and put it in the
header menu with anchor text matching its title.

**Header menu:** the live header renders `halara-inspired-menu` (confirmed in
`sections/header-group.json`), *not* `main-menu`. Edit that one. Note it
currently sends "Pants" to `daily-casual` and "Best Seller" to `bestsellers`
rather than `best-sellers`.

## 6. HIGH — Unpublish the duplicates and the catch-alls

Verified byte-identical by comparing product counts and the first ten product
handles in order:

- `denim` (30) and `denim-style` (30) — identical membership, identical order
- `work-commute` (38) and `city-commute` (39) — identical first ten
- `all-product`, `empty`, `optimize` (194 each) — SEO-app scratch collections

Published catch-alls with no SEO and no description: `all` (title "Products",
402 products — the whole catalogue), `avada-best-sellers` (title "Best Sellers",
401), `shop-all` (38). `avada-best-sellers` collides on title with
`best-sellers` and near-collides with `bestsellers`: **three published URLs all
presenting as the best-sellers page.**

**Do:** unpublish `all`, `avada-best-sellers`, `all-product`, `empty`,
`optimize`, `shop-all` from the Online Store channel — leave them existing so
the apps keep working. Delete `denim-style` and `city-commute` with 301s to
their twins.

## 7. HIGH — Empty and thin collections

Zero products, published: `swim`, `plus-size`.

Under five products: `buy-2-get-32-off` (1), `buy-1-get-1-free` (1),
`buy-2-10-off-buy-3-20-off` (1), `wedding` (2), `cargo-pants` (2),
`flowy-shorts` (2), `party` (3), `9-shorts` (3), `seamless-flow-leggings` (3),
`gymshark-demo-leggings-with-pockets` (3), `denim-leggings` (4),
`straight-leg-jeans` (4), `jean-shorts` (4), `butt-lifting-shorts` (4),
`active-pants` (4).

That is 18 collections — 20% of the catalogue — that are crawlable dead ends.

**Do:** unpublish all of them except `plus-size`, which should be filled rather
than hidden if you intend to compete for the plus-size query Halara owns.

## 8. MEDIUM — Promo sprawl

Eight promo collections compete for one job: `buy-2-get-1-free` (82),
`buy-3-for-59` (25), `buy-2-for-69` (24), `buy-2-for-59` (15), `buy-3-for-99`
(7), `buy-2-get-32-off` (1), `buy-1-get-1-free` (1),
`buy-2-10-off-buy-3-20-off` (1).

Halara gets a sitelink for "Buy 2, Get 1 Free" because it is *one* page with one
clear name. **Do:** keep `buy-2-get-1-free` as the single public promo page,
give it a proper title and description, link it from the header, and unpublish
the rest.

## 9. MEDIUM — Delete the unrendered menus

Ten menus exist; the live theme renders three (`halara-inspired-menu`,
`main-menu`, `footer`). Delete `gymshark-leggings`, `main-menu-copy`,
`main-menu-first`, `pill-shop`, `pill-help`, `links`. Leave
`customer-account-main-menu` — Shopify requires it.

---

## Expected timeline

Sitelinks are not switched on. Google re-derives them as it recrawls and
re-evaluates site structure, so expect to see movement over several weeks after
the navigation and SEO changes are live, not days — and expect nothing at all
while 46 scraped blog articles are still published, because site-level quality
gates the whole thing. Do `worklist-blog-cleanup.md` first.
