# Making Celeste L'Amour read as a real brand on Google

Audited 2026-09-24 against the Shopify Admin API. **Nothing in this directory
has been executed. The live store has not been touched.**

---

## The question

> When people look up Celeste L'Amour on Google, I want them to find a legit
> brand like Halara and Alo — and I want Google to give a breakdown of my brand.

Today Google's AI Overview for "celeste lamour" returns **L'amour Nails & Spa,
a nail salon in the Bronx**, and the image block returns a Brocéliande
colouring book, a perfume bottle and a pair of sandals.

## The answer, in one paragraph

This is not a markup problem. Your theme already emits Organization, WebSite,
Product, Article and BreadcrumbList JSON-LD — more than most Shopify stores
ever get. The problem is that **celestelamour.com currently tells Google it is
a different company.** Of 356 active products, 170 carry the vendor `Gymshark`
and are published on your domain with `gymshark-` in the URL. Nine published
collections serve Gymshark's own meta descriptions. Until recently, 45 of 48
published blog articles were scraped college-admissions content from
PrepScholar and Ivy Coach, stamped with your brand as `publisher`.

Google builds a brand entity from the preponderance of what a domain says about
itself. The plurality answer on your domain has been *Gymshark*, with a side of
SAT prep. There is no amount of schema that overrides that, because schema is a
claim and the catalogue is evidence.

**So the method is not "add structured data". It is: stop contradicting
yourself, then make the true facts easy to find, then get them corroborated
off-site.** In that order, because each step is wasted without the one before.

---

## What was found

Everything below was pulled from the Admin API, not inferred. Severity is by
what it costs you, not by how alarming it sounds.

| # | Finding | Scale |
|---|---|---|
| 1 | **Products branded Gymshark**, published, `gymshark-` in the URL, `"brand":"Gymshark"` in JSON-LD. Each carries a `gymshark.source_url` metafield pointing at the live Gymshark product page. | 170 of 356 |
| 1b | **Halara's registered sub-brand names in image alt text** (UltraSculpt, SoftlyZero, Breezeful, HeatCore…) | 117 of 356 |
| 1c | **Fabricated review aggregates in metafields.** Flagship holds 4.8 / 37,118 against zero real reviews. **Nothing renders them** — see the correction below — but they are one wiring change from being real. | ~178 products |
| 3 | **Collections carrying Gymshark's verbatim SEO copy** — and the only collections with SEO copy at all | 9 of 90 |
| 4 | **Collections with no internal links from any sitewide surface** | ~72–80 of 90 |
| 5 | **Collections with no SEO title or description** | 80 of 90 |
| 6 | **Products with no SEO title or description** | 353 of 356 |
| 7 | **Homepage links to exactly one collection**, and points 10 CTAs at a single product | — |
| 8 | **`shop.description` is null** — no store meta description exists | — |
| 9 | **Scraped blog articles** (deleted mid-audit; index cleanup still outstanding) | 45 of 57 |
| 10 | **Three different published contact emails**, one misspelled, two a Gmail address | — |
| 11 | **Live Terms of Service** still contains Shopify's `[NOTE TO MERCHANT: …]` scaffolding and `[LINK]` placeholders | — |
| 12 | **Blog author renders as a schema.org Person named "5K20RB-1R"** — your myshopify subdomain | 3 of 5 articles |
| 13 | **URL redirects pointing at the bare homepage** — Google treats these as soft 404s | ≥7 of 328 |

### Corrections I made to my own work

Recorded because the reasoning is more useful than a clean first draft.

- **The fake reviews, twice.** I first called them "latent, not live" — I had
  checked `reviews.*` and `judgeme.*` and missed `air_reviews_product`. I then
  found that namespace plus a snippet reading it, and said ratings were
  rendering live on the flagship. **Also wrong.** `main-product.liquid` line 160
  renders `rating.liquid`, which reads only `reviews.rating` (null here) and is
  gated so a nil rating emits nothing. The snippet I traced,
  `gs-buybox-rating.liquid`, does read the fabricated values — but is
  referenced nowhere. I inferred a render path from a filename instead of
  reading the 137 KB section file. Full trace in
  `google/worklist-fake-ratings.md`.
- **A `sameAs` bug.** Already fixed in the theme published mid-session, and my
  framing of empty `sameAs` entries as harmful was folklore — Google ignores
  them. Withdrawn.
- **Scaled-content policy claims.** Several findings about the scraped blog
  were refuted on re-query, because the articles had been deleted while the
  audit ran. The underlying finding was real — I enumerated all 57 myself
  beforehand — but the *policy violation* framing no longer describes a live
  state. `google/worklist-blog-cleanup.md` was rewritten accordingly.

---

## The method

### Phase 1 — Stop contradicting yourself (week 1, deletions only)

Every item here is a removal. Nothing new gets written. This is deliberate: you
cannot establish an entity while the evidence points elsewhere.

- Delete or reclassify the 170 Gymshark products → `google/worklist-competitor-products.md`
- Unpublish the 10 `gymshark-demo-*` collections and clear their Gymshark SEO copy
- Unpublish `halara-leggings`, rename the ™ handles, replace Halara-CDN images
- Unpublish the empty, thin, duplicate and catch-all collections → `google/worklist-collections-sitelinks.md`
- Delete the two empty published blog articles; fix the `5K20RB-1R` bylines
- Search Console → **check for a manual action first**, then prefix-remove the dead URLs → `google/google-tools-setup.md`

### Phase 2 — Defuse the loaded guns (week 1–2, deliberate not urgent)

Fabricated data sitting in the store with no render path today, one wiring
change from being real. Worth clearing deliberately; not worth dropping
everything for.

- Delete the ~178 fabricated `air_reviews_product` aggregates
- Delete the orphan `gs-buybox-rating.liquid`, which reads them and is named as
  though it belongs in the buy box
- Delete the 100 DEMO Judge.me rows; confirm Judge.me rich snippets are OFF
- Delete the disabled template sections: two duplicate invented testimonial
  walls, a comparison table, and unsubstantiated fabric claims

→ `google/worklist-fake-ratings.md`

### Phase 3 — Say who you are (weeks 2–4)

Now the facts have nothing competing with them.

- Set `shop.description` and the store title → `shopify/store-identity-values.md`
- Standardise the brand name on `Celeste L'Amour` (straight apostrophe — 185 of 186 products already use it)
- Fix the three conflicting contact emails; clean the `[NOTE TO MERCHANT]` text out of Terms
- Publish an About page written so its first sentence is liftable → `content/about-page.html`
- Write real titles, descriptions and body copy for the 8 sitelinks-candidate collections
- Rebuild the homepage and header to link categories rather than one product

### Phase 4 — Deploy the markup (week 4)

Last, not first. Declaring a rich Organization entity while the catalogue
contradicts it asks Google to resolve a conflict it will resolve against you.

- `theme/snippets/brand-organization.liquid` — new Organization + OnlineStore + WebSite
- `theme/snippets/meta-tags.liquid` — revised drop-in replacement
- `theme/templates/robots.txt.liquid` — new

### Phase 5 — Get corroborated (ongoing, months)

This is what actually produces the Halara-style AI Overview sentence, and it
cannot be done inside Shopify.

Google can write *"Halara is a popular online direct-to-consumer women's
athleisure brand. Founded in 2020 and headquartered in Hong Kong"* because
those facts sit in Wikipedia, Wikidata, Crunchbase, PitchBook, ZoomInfo and
LinkedIn, plus trade press — all agreeing. Not because of Halara's markup.

Order: LinkedIn company page → Crunchbase → D-U-N-S → state registration
consistency → Wikidata (only once the others exist) → trade coverage.

→ `google/google-tools-setup.md`

---

## What to expect, honestly

| Outcome | Realistic? | When |
|---|---|---|
| Correct title + description in results | Certain | Days |
| Ranking #1 for "Celeste L'Amour" | Very likely | 2–6 weeks after Phase 1 |
| Site name rendering as "Celeste L'Amour" | Likely | 2–8 weeks |
| A sitelinks block | Plausible | 1–3 months after Phase 3 |
| Product rich results (price, availability) | Yes | Weeks, once markup and feed agree |
| AI Overview describing the brand correctly | Plausible | Follows Phase 5. Months. |
| A knowledge panel | **Not a deliverable** | Emergent. May never happen at this size. |
| Review parity with Halara (~482k Trustpilot) | **No** | Not a goal worth having |

Two things you cannot buy or request: a knowledge panel and sitelinks. Both are
outputs. Anyone selling you either is selling you nothing. And Alo's map pack
in your screenshot comes from having physical stores — that one is not a markup
gap.

---

## Files

```
celeste-google-presence/
├── README.md                                  this file
├── google/
│   ├── worklist-fake-ratings.md               Phase 2 — defuse before it fires
│   ├── worklist-competitor-products.md        Phase 1 — start here: 170 Gymshark products
│   ├── worklist-collections-sitelinks.md      Phase 1/2 — collections + navigation
│   ├── worklist-blog-cleanup.md               Phase 1 — post-deletion tail
│   └── google-tools-setup.md                  Phase 1/4 — Search Console, off-site
├── shopify/
│   └── store-identity-values.md               Phase 2 — copy/paste admin values
├── content/
│   └── about-page.html                        Phase 2 — brand-entity source page
└── theme/
    ├── snippets/brand-organization.liquid     Phase 3 — new
    ├── snippets/meta-tags.liquid              Phase 3 — replacement
    └── templates/robots.txt.liquid            Phase 3 — new
```

## How this was audited

`celestelamour.com` is blocked by this environment's network policy, so the
site could not be crawled. The audit ran against the **Shopify Admin API**:
store settings, all 402 products, all 90 collections, both blogs, all 11 pages,
the live theme's Liquid and section JSON, navigation menus, publications and
shop metafields. That is a better source than rendered HTML — it shows the data
behind the page, including what is one toggle from going live.

Findings were produced by six independent auditors and then adversarially
verified, which caught several errors in the first pass — including that the
store changed underneath the audit. The live theme was republished and the
scraped blog deleted while it ran. Where verification contradicted a finding,
the finding was withdrawn rather than reworded.
