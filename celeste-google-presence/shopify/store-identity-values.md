# Shopify admin values — copy/paste

Everything here is a field you change in the Shopify admin. No code, no deploy.
These are the highest-leverage-per-minute items in the whole plan, because
several of them are what Google literally prints on the search result page.

Each entry names the exact screen, the exact field, the current value pulled
from the Admin API on 2026-09-24, and the value to set.

---

## 1. Store meta description — currently EMPTY

**Screen:** Online Store → Preferences → *Title and meta description*
**API field:** `shop.description`
**Current value:** `null`

This is the most direct miss in the entire audit. It is the text Google shows
under the store name for a brand search. Halara has one, Alo has one, Celeste
L'Amour has nothing — so Google composes a snippet from whatever homepage prose
it finds. Right now it is pulling the "Celeste means of the sky…" paragraph,
which is lovely brand writing but says nothing about what the company sells,
where it ships, or that it takes returns.

**Set it to (148 characters):**

```
Celeste L'Amour makes sculpting leggings, shorts and bras with real tummy control and buttery-soft stretch. Free US shipping over $75. 30-day returns.
```

Why this shape: category noun first ("sculpting leggings, shorts and bras") so
the snippet answers "what is this company"; a concrete product claim; then two
trust facts. The shipping and returns figures are taken from the store's own
published policies, so they are true. Keep it under about 160 characters or
Google truncates it.

**Also set, on the same screen — store title:**

```
Celeste L'Amour | Sculpting Leggings, Shorts & Bras
```

Not just "Celeste L'Amour". The homepage title is a ranking and disambiguation
signal, and a bare brand name gives Google nothing to distinguish this from
"L'amour Nails & Spa" — which is the entity Google's AI Overview currently
returns for the query.

---

## 2. Vendor field — fragmented across the catalogue

**Screen:** Products → (each product) → Product organization → Vendor
**API field:** `product.vendor`

Confirmed distinct values in use: `Celeste L’Amour` (typographic apostrophe,
U+2019), `CELESTELAMOUR` (all caps, no spaces), and `Celeste L'Amour`
(straight apostrophe, in the `custom.pdp_brand_name` metafield).

This matters more than it looks. `product.vendor` is what the theme writes into
Product JSON-LD as `brand.name`. Every distinct string is a separate brand to
Google's entity graph, so the catalogue is currently split across three brands,
none of which accumulates the full signal.

**Canonical form — use this exact string everywhere:**

```
Celeste L’Amour
```

That is the typographic apostrophe U+2019, matching `shop.name`. Pick it and
never deviate: Shopify store name, every product Vendor, Merchant Center brand
attribute, every social profile display name.

Bulk-edit path: Products → filter by Vendor → select all → Bulk edit → Vendor.
Do it one vendor value at a time.

Note the alternate spellings are not wasted — they go in the `alternateName`
array in `theme/snippets/brand-organization.liquid`, which is the correct way
to tell Google "these strings are the same entity" without fragmenting the
canonical one.

---

## 3. Contact email — three different addresses are published

**API field:** `shop.contactEmail`, plus the policy bodies.

Confirmed, all currently live:

| Where | Address |
|---|---|
| Shopify contact email field | `administrator@celestelamour.com` |
| Contact policy page | `adminstrator@celestelamour.com` — **misspelled**, missing the second `i` |
| Privacy policy page | `adminstrator@celestelamour.com` — same misspelling |
| Refund policy page | `celestelamourvirtue@gmail.com` |
| Shipping policy page | `celestelamourvirtue@gmail.com` |

Two separate problems. The misspelled address almost certainly bounces, so
anyone using the Contact or Privacy page to reach the company gets nothing. And
a free Gmail address as the published support contact on the pages that handle
returns and shipping is a legitimacy signal that reads exactly the way you do
not want it to read — it is one of the standard heuristics people and
review-aggregators use to flag a dropshipper.

**Fix:** pick one branded address (`support@celestelamour.com` is the
conventional choice), create it, then update: Settings → General → Store contact
email, and the body text of all four policy pages under Settings → Policies.

---

## 4. Legal / Terms pages — unreplaced template placeholders are public

**Screen:** Settings → Policies → Terms of service

The live Terms of Service contains Shopify's own editorial scaffolding, visible
to any visitor:

- Section 9 opens with: `[NOTE TO MERCHANT: This section accurately characterizes Shopify's relationship with your store and should not be removed or modified.]`
- Sections 3, 10 and the overview contain unreplaced `[LINK]` placeholders,
  e.g. `our Privacy Policy [LINK]` and `our Refund Policy [LINK]`.

Delete the `[NOTE TO MERCHANT: …]` line entirely. Replace each `[LINK]` with the
real URL (`https://celestelamour.com/policies/privacy-policy`,
`https://celestelamour.com/policies/refund-policy`).

Also fill in the Contact policy's empty fields — it currently publishes
`VAT number:` and `Trade number:` with nothing after them. Either populate them
or remove the lines.

None of this is an SEO ranking factor. It is a trust factor, and trust is the
actual thing being asked for here. A legal page carrying the vendor's own
"note to merchant" tells a careful reader the company did not read its own
terms.

---

## 5. Trade name in the Contact policy

Currently `Celeste L’Amour`. The registered entity is `VIRTULIFT LLC`, which is
the name that appears on customers' card statements.

Add a line so the two are connected in public:

```
Celeste L’Amour is a trading name of VIRTULIFT LLC, 2605 S Indiana Ave, Unit 201, Chicago, IL 60616, United States.
```

This is also what makes the `legalName` property in the Organization schema
corroborated rather than asserted — Google gives more weight to a structured-data
claim that is repeated in visible page text.

---

## 6. Product status and duplicates

**Confirmed:** 357 active, 42 draft, 0 archived, 402 total.

Four separate products share the title `Celeste Sculpt Scrunch Leggings`, with
handles:

- `celeste-sculpt-scrunch-leggings`
- `celeste-sculpt-scrunch-leggings-copy`
- `celeste-sculpt-scrunch-leggings-copy-copy`
- `celeste-sculpt-scrunch-leggings-copy-copy-copy-copy`

A handle ending in `-copy-copy-copy-copy` is visible in the URL bar and in
search results. Keep one canonical product per style; for the rest either
delete them, or if they are live promo variants (Buy 2 for $59 / $69), give
them distinct titles and set the canonical to the primary product.

Full duplicate-group list is in `../google/worklist-duplicates.md` once the
catalogue scan completes.
