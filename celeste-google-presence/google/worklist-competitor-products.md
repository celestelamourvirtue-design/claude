# The 170 Gymshark products — start here

Verified against the Shopify Admin API, 2026-09-24. **Nothing here has been
executed.**

---

## The number

```
productsCount(query: "status:active")                          = 356
productsCount(query: "status:active AND vendor:Gymshark")      = 170
productsCount(query: "status:active AND vendor:Celeste L'Amour") = 185
productsCount(query: "status:active AND vendor:Celeste L’Amour") =   1
```

**170 of your 356 active products — 48% — carry the vendor `Gymshark`.**

They are not drafts and they are not hidden. Sampled `onlineStoreUrl` values,
returned live by the API:

```
https://celestelamour.com/products/gymshark-everyday-seamless-leggings-leggings-blue-aw26-b7a3l-uctn
https://celestelamour.com/products/gymshark-everyday-seamless-flared-legging-leggings-black-aw25
https://celestelamour.com/products/gymshark-training-straight-leg-legging-leggings-black-aw25
https://celestelamour.com/products/gymshark-cotton-blend-seamless-flared-leggings-leggings-grey-aw26
```

All published 2026-09-17.

## Why this is the single thing standing between you and a brand entity

Three separate signals, all pointing the same way, on nearly half your site:

1. **The URL.** The handle begins `gymshark-`. The competitor's brand name is
   in the path of a celestelamour.com page.
2. **The structured data.** `snippets/meta-tags.liquid` on the live theme
   emits, on every product page:

   ```liquid
   "brand": { "@type": "Brand", "name": {{ product.vendor | json }} }
   ```

   With `product.vendor` = `Gymshark`, that renders
   `"brand":{"@type":"Brand","name":"Gymshark"}` — a machine-readable
   declaration, on 170 pages, that the brand behind this product is Gymshark.
3. **The collections.** Nine published `gymshark-demo-*` collections carry
   Gymshark's own verbatim title tags and meta descriptions, and they are the
   only collections on the store with SEO copy written at all.

You asked why Google returns a Bronx nail salon for "celeste lamour" instead of
building you a brand panel. This is why. Google builds a brand entity from the
preponderance of what a domain says about itself. Right now the plurality
answer on celestelamour.com is *Gymshark*.

No amount of Organization schema fixes this. Schema is a claim about the
brand; 170 product pages are evidence about the brand, and evidence wins.

## It is also a trademark exposure

Gymshark is a registered mark. Publishing 170 product pages whose URLs, titles
and structured data carry it — alongside nine collection pages reproducing
Gymshark's own marketing copy verbatim — is not an SEO problem you can weigh
against a ranking benefit. That is a decision to take on its own terms, and
this file is not legal advice. But the SEO and the legal answer happen to be
the same one, which makes it easy.

Sampled collection images also carry Halara's CDN derivative naming
(`-342x.webp`), and one product image is stored under a filename containing
`mpir.halarastatic.com`.

---

## What to do

### Decide first: are these products you actually sell?

Everything below branches on one question, and only you can answer it.

**If they are dropship listings you never intended to fulfil** — most likely,
given the AW23/AW25/AW26 season codes and the bulk 2026-09-17 publish
timestamp — then delete them. Not unpublish: delete. They are 48% of your
catalogue and they are describing a different company.

**If you genuinely resell Gymshark stock**, you are a retailer, not a brand, and
the fix is different: the products stay but the `vendor` field is still wrong
for entity purposes. You would keep `Gymshark` as vendor (it is accurate), stop
trying to rank celestelamour.com as a brand for those pages, and separate your
own-brand catalogue into its own clearly-branded section. Say so and I will
rework this file for that case.

The rest of this assumes the first answer.

### Step 1 — Delete, do not unpublish

Products → filter Vendor is `Gymshark` → select all 170 → Delete.

Unpublishing leaves the URLs returning 404 while the products linger in the
admin, and leaves them in any feed that reads product status rather than
publication. Deleting is cleaner.

### Step 2 — Do NOT bulk-redirect them to the homepage

You already have **328 URL redirects**, and at least seven of them point at the
bare homepage `/`:

```
/products/lightly-lined-bra                     -> /
/products/wholesale-plus-size-full-body-shaper  -> /
/collections/shapewear...                       -> /
```

Google treats an irrelevant redirect as a soft 404 — it does not pass anything,
and a large set of them is itself a pattern associated with manipulation. Let
the deleted product URLs 404. Then use Search Console → Removals on the
`/products/gymshark-` prefix to get them out of results quickly while the 404s
are processed.

While you are in there, review the 328 redirects and repoint or remove the
homepage ones.

### Step 3 — Fix the collections

Covered in `worklist-collections-sitelinks.md`: unpublish the ten
`gymshark-demo-*` collections and clear their Gymshark SEO copy, delete the
unrendered `gymshark-leggings` navigation menu, and unpublish `halara-leggings`.

### Step 4 — Standardise the vendor field on the remaining products

After the deletion you are left with 186 own-brand products split across two
spellings:

| Value | Count |
|---|---:|
| `Celeste L'Amour` (straight apostrophe, U+0027) | 185 |
| `Celeste L’Amour` (typographic apostrophe, U+2019) | 1 |

**Standardise on the straight apostrophe: `Celeste L'Amour`.**

This reverses what I recommended in `../shopify/store-identity-values.md`
before I had the counts, and the counts settle it. 185 products already use the
straight form against 1 using the typographic one, so the cheap direction is
obvious. The straight apostrophe is also the more robust character: it survives
copy-paste, feed exports, CSV round-trips and URL encoding without turning into
`â€™`, which U+2019 regularly does.

So: change the one outlier product, and change **Settings → General → Store
name** from `Celeste L’Amour` to `Celeste L'Amour` so `shop.name` agrees. One
field beats 185 edits.

Both spellings still belong in the `alternateName` array in
`../theme/snippets/brand-organization.liquid` — that is the correct place to
tell Google the variants are one entity, and it costs nothing.

### Step 5 — Then, and only then, the schema work

`../theme/snippets/brand-organization.liquid` and the revised
`../theme/snippets/meta-tags.liquid` are worth deploying — but deploy them
after this cleanup, not before. Declaring a rich Organization entity while 170
pages declare a different brand is asking Google to resolve a contradiction it
will resolve against you.

---

## Sequence

1. This file — delete the 170, fix the vendor field.
2. `worklist-collections-sitelinks.md` — unpublish competitor collections, fix navigation.
3. `worklist-blog-cleanup.md` — finish the post-deletion steps.
4. `../shopify/store-identity-values.md` — store name, meta description, contact details.
5. Theme schema deploy.
6. `google-tools-setup.md` — Search Console removals, manual action check, Merchant Center.
