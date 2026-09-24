# The Google-side work — what you do outside Shopify

Everything here happens in Google's own tools or on third-party sites. None of
it is code. **Nothing here has been executed.**

---

## 0. Two things to stop believing first

**You cannot request a knowledge panel.** There is no form, no submission, no
purchase. A knowledge panel is an *output* of Google having a confident node in
its Knowledge Graph for "Celeste L'Amour". Claiming/verification only becomes
available once a panel already exists. Anyone selling you one is selling you
nothing.

**You cannot request sitelinks either.** They are generated from your site's
own structure and internal linking. The demotion tool that used to exist in
Search Console was removed in 2016. The only lever is the work in
`worklist-collections-sitelinks.md`.

So the realistic framing: you are not asking Google for a brand panel. You are
removing the reasons Google currently cannot build one, and supplying the
corroborating facts it needs. Those are things you control.

---

## 1. Search Console — do these in order

### a. Check for a manual action. First. Before anything.

**Security & Manual Actions → Manual actions.**

The blog that held 45 scraped articles has been deleted, but the question is
whether it was noticed before it went.

- **"No issues detected"** → the effect was algorithmic. It lifts on its own as
  Google recrawls. Weeks. Nothing to file.
- **"Thin content with little or no added value"** or **"Pure spam"** → deletion
  does not lift it. File a reconsideration request describing exactly what was
  removed and what changed. Recovery is weeks *after* a human reviews it.

This one check determines your whole timeline, which is why it is first.

### b. Remove the deleted URLs from the index

**Removals → New request → Remove all URLs with this prefix:**

```
https://celestelamour.com/blogs/verbs-list/
```

And, after the Gymshark products are deleted:

```
https://celestelamour.com/products/gymshark-
```

Removal hides them within about a day and lasts roughly six months — enough
time for the 404s to be processed permanently. Without this, 45 plagiarised
URLs and 170 competitor-branded ones sit in the index for months while Google
patiently re-checks them.

### c. Set the site name

Your `WebSite` structured data already declares a name, so this is mostly about
making the signals agree. Google's site-names system reads the `WebSite`
JSON-LD `name`, `og:site_name`, the `<title>` and homepage heading text. Make
all four say `Celeste L'Amour` — same spelling, straight apostrophe. See
`../shopify/store-identity-values.md`.

### d. Submit the sitemap and watch coverage

`https://celestelamour.com/sitemap.xml`. Then watch **Pages → Why pages aren't
indexed** over the following weeks. "Duplicate without user-selected canonical"
appearing in bulk is the signal that the collection consolidation work has not
gone far enough.

---

## 2. Google Business Profile — **do not create one**

My two research passes disagreed on this, so here is the resolution, because
getting it wrong is actively harmful.

One pass called GBP "the single highest-leverage item because it is a
Google-owned property". That reasoning is wrong for this business.

Google Business Profile eligibility requires the business to **make in-person
contact with customers during its stated hours**. An online-only DTC brand
operating from an LLC office address at 2605 S Indiana Ave, Unit 201 does not
meet that. Creating a profile there invites suspension, and a suspended profile
is a worse signal than no profile — it is a Google-side record of a guidelines
violation attached to your business name.

**The only legitimate exception:** if Celeste L'Amour genuinely does meet
customers in person — pop-ups, local pickup, in-person fittings — then register
as a **service-area business**, which hides the street address and declares a
service region instead. Be ready to verify.

If a profile has already been created at that address, remove it rather than
wait for suspension.

---

## 3. The off-site corroboration layer — this is the actual lever

This is the part that produces the Halara-style AI Overview sentence, and it is
the part that cannot be done in Shopify.

Google writes *"Halara is a popular online direct-to-consumer women's athleisure
and casual apparel brand. Founded in 2020 and headquartered in Hong Kong…"*
because those facts exist in **Wikipedia, Wikidata (Q136359497), Crunchbase,
PitchBook, CB Insights, ZoomInfo and LinkedIn**, plus trade coverage in Modern
Retail, Marketing Brew and Business Insider. The sentence is not generated from
Halara's markup. It is assembled from independent records that agree.

Celeste L'Amour has none of those. That is the gap.

Build it in this order — each step is a prerequisite for the next, because
later sources cite earlier ones:

1. **Publish the canonical brand description on your own site.** Nothing can
   cite you until a citable source exists. `../content/about-page.html` is
   drafted; fill in the founding year and the fabric paragraph.
2. **LinkedIn company page.** Free, no editorial gate, and a source Google's
   entity graph reads directly for "founded" and "headquartered". List
   VIRTULIFT LLC, Chicago, Retail Apparel. Highest value per minute of
   anything on this list.
3. **Crunchbase organization profile.** Free contributor account. Founding
   date, location, website, category.
4. **D-U-N-S number** (free from Dun & Bradstreet). This is what populates the
   `duns` identifier in your Organization markup and appears in business
   databases.
5. **Illinois Secretary of State LLC record** for VIRTULIFT LLC — this already
   exists as a public record; make sure the name and address match what you
   publish everywhere else.
6. **Trade coverage.** The hard one. Not buyable, not fakeable, and the thing
   that actually separates Halara from you.

### Wikidata — yes, but not yet

The Wikidata bar is *verifiable existence*, not fame — so a small DTC brand can
qualify, unlike Wikipedia, where you would be speedy-deleted for notability.

But creating a Wikidata item today, with zero independent citable references,
from a fresh account, reads as promotional and gets deleted. Do steps 1–5
first. Then create the item with P31 (instance of) = business, P571
(inception), P159 (headquarters) = Chicago, P17 = United States, P856 (official
website), P452 (industry), citing the Crunchbase, LinkedIn and state
registration records as references.

**Do not attempt a Wikipedia article.** It will fail notability and be deleted,
and a deletion discussion is a permanent public record attached to your brand.

---

## 4. Merchant Center

The Google & YouTube channel is already installed on your store. Product rich
results and the merchant treatments need more than Product markup:

- **Clean product identifiers.** Many variants carry supplier SKUs like
  `191288010:-1#Pink;191288664:28313#Xs`, and many carry none. Replace with
  stable internal SKUs (`CLA-ULTRASCULPT-BLK-M`). Set `gtin`/`mpn` only where
  the supplier gives you real ones — **leave them out rather than invent
  them**; a wrong GTIN is worse than an absent one.
- **Shipping and returns configured in Merchant Center**, matching what the
  site says. The revised `meta-tags.liquid` emits shipping and return details
  taken from your published policies; if Merchant Center says something
  different, Google cross-checks and can suppress the annotation for the whole
  domain.
- **Fix the product category.** At least one product has
  `mm-google-shopping.google_product_category = 204`. Verify that against
  Google's product taxonomy and set the correct leaf category for activewear
  rather than a generic parent.
- **Reviews.** Product review stars in Merchant Center need a real review
  corpus. See below.

---

## 5. Reviews — containment before accumulation

**Containment, do this now:** in Judge.me → Manage Reviews, filter for bodies
containing `DEMO` and delete the 100 rows on product 7830848110643. Delete, do
not unpublish — Judge.me's own rich-snippet feature reads the underlying store,
not your theme, so unpublishing does not reliably remove them from markup.

Then confirm **Judge.me → Settings → Rich snippets** is OFF until you have a
real corpus. Your theme's guard does not cover what the app emits on its own.

**Accumulation:** turn on the post-fulfilment review request with a ~14-day
delay, pointed at the flagship product. For scale: Halara carries roughly 482,000
Trustpilot reviews against your 142 Judge.me rows, 100 of which are demo data.
You are not closing that gap. You do not need to — you need enough genuine
reviews on your top products to earn stars, which is dozens, not thousands.

---

## 6. What to actually expect, on what timeline

Honest calibration, because the difference between these matters for planning:

| Outcome | Realistic? | When |
|---|---|---|
| Correct meta description + title in results | Yes, certain | Days after the change |
| celestelamour.com ranking #1 for "Celeste L'Amour" | Yes, very likely | 2–6 weeks after cleanup |
| Site name rendering as "Celeste L'Amour" | Yes, likely | 2–8 weeks |
| A sitelinks block | Plausible | 1–3 months after the navigation work |
| Product rich results (price, availability) | Yes | Weeks, once markup + feed agree |
| AI Overview describing the brand correctly | Plausible | Follows the corroboration layer, months |
| A knowledge panel | Not a deliverable | Emergent; may never happen at this size |
| Review parity with Halara | No | Not a realistic goal |

The first four are within your control and worth doing. The knowledge panel is
not something to plan around — and notably, **Alo Yoga's map pack in your
screenshot comes from having physical stores**, which is not a gap you can
close with markup.

---

## Sequence across all files

1. `worklist-competitor-products.md` — the 170 Gymshark products. Biggest item.
2. `worklist-collections-sitelinks.md` — competitor collections, navigation, SEO.
3. `worklist-blog-cleanup.md` — the post-deletion tail.
4. `../shopify/store-identity-values.md` — store name, meta description, contacts.
5. This file, §1 — Search Console: manual action check, then removals.
6. `../content/about-page.html` — publish it.
7. Theme deploy — `brand-organization.liquid` + revised `meta-tags.liquid`.
8. This file, §3 — the off-site corroboration layer. Slowest, highest ceiling.
