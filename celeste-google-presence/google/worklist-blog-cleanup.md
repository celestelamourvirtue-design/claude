# Blog cleanup — mostly done, finish the tail

**This file was rewritten. The bulk deletion it originally described has
already happened.**

When I first enumerated the blog earlier in this session it held **57
articles**, of which **45 were scraped third-party content** — PrepScholar,
Ivy Coach, College Transitions, Shemmassian — published under the byline
"Victoria Lamar" on `templateSuffix: ceg-article`. Titles like "The Easy Trick
to Convert Celsius to Fahrenheit · PrepScholar" and "Best Analysis: The
American Dream in The Great Gatsby · PrepScholar".

Re-querying now returns:

```
blog "News" (handle verbs-list, gid://shopify/Blog/89583812659)
  articlesCount = 12  (precision EXACT)
blog "The Comfort of Body Shapers..." (gid://shopify/Blog/90119045171)
  articlesCount = 2
store-wide articles(first:50) -> 14 nodes, hasNextPage false
```

57 − 12 = 45. The scraped set is exactly what is missing. **Someone deleted
them during this session.** Good — that was the right call and it was the
highest-priority item on the list.

What follows is the part that deletion alone does not finish.

---

## 1. The deleted URLs are still in Google's index

Deleting a Shopify article makes its URL return **404**. Google treats 404 as
"maybe temporary" and will keep the URL in its index, and keep retrying it,
for a long time. Forty-five plagiarised URLs sitting in the index attributed
to your domain are still doing damage while they linger.

**Do this now, in Search Console:**

1. **Removals → New request → Remove all URLs with this prefix**, and submit:
   ```
   https://celestelamour.com/blogs/verbs-list/
   ```
   This hides everything under that path from results within about a day. The
   removal lasts roughly six months — ample time for the 404s to be processed
   as permanent.

2. **Do not** add `Disallow: /blogs/verbs-list/` to robots.txt as a substitute.
   Blocking the crawl stops Google discovering that the pages are gone, and
   indexed URLs can persist indefinitely as bare links with no snippet. Crawl
   control and index control are different things. There is a longer note on
   this in `../theme/templates/robots.txt.liquid`.

3. **Do not** bulk-redirect them anywhere. See the note on the 328 existing
   redirects in `worklist-competitor-products.md` — seven already point at the
   bare homepage, which Google handles as a soft 404.

## 2. Check for a manual action — before anything else

**Search Console → Security & Manual Actions → Manual actions.**

- If it lists **"Thin content with little or no added value"** or **"Pure
  spam"**, deletion does not lift it. You must file a reconsideration request
  describing what was removed and what changed. Recovery is then weeks *after*
  a human reviews it.
- If it says **"No issues detected"**, any effect was algorithmic and lifts on
  its own as Google recrawls. Weeks, no request needed.

This single check tells you which timeline you are on, so do it before
investing in anything downstream.

## 3. Rename the blog — its handle is still a leftover

The blog is titled **News** but its handle is **`verbs-list`**, so it lives at
`celestelamour.com/blogs/verbs-list/`.

That handle came from the scraped article "229 Common English Verbs With
Examples · PrepScholar" — PrepScholar publishes it at
`blog.prepscholar.com/verbs-list`, the identical slug. The blog was named after
an ingested article and the name outlived the articles.

**Do:** Online Store → Blog posts → Manage blogs → News → change the handle to
`journal`. Leave "Create a URL redirect" checked so `/blogs/verbs-list` →
`/blogs/journal` is written automatically. This is the one redirect in this
whole plan that is correct to create, because it is a genuine equivalent.

## 4. Clean up the 5 published articles that remain

| Handle | Author as stored | Problem |
|---|---|---|
| `pagefly-blog` | `PageFly` | Title is literally "pagefly blog". App test artifact. **Body is empty.** Delete. |
| `article-dec-14-2025` | `Mory Keita` | Title is "Article Dec 14, 2025" — an untouched placeholder. **Body is empty.** Delete or write it. |
| `expert-tips-for-selecting-shapewear-post-surgery` | `5K20RB-1R` | On-topic. Fix the author. Medical-adjacent — must not imply clinical benefit. |
| `fleece-shapewear-a-winter-fashion-revolution` | `5K20RB-1R` | On-topic. Fix the author. |
| `the-comfort-of-body-shapers-why-you-need-them-468` | `Celeste L'Amour` | On-topic, correct author. The handle has a stray `-468` suffix; tidy it. |

Two of the five published articles have **completely empty bodies**. A
published URL with a title and no content is a thin-content page in the most
literal sense.

### The author field is worse than it looks

`5K20RB-1R` is your myshopify subdomain (`5k20rb-1r.myshopify.com`) in
capitals. The live theme's `snippets/meta-tags.liquid` emits on every article
page:

```liquid
"author": { "@type": "Person", "name": {{ article.author | json }} }
```

So Google is currently being told there is a **schema.org Person named
"5K20RB-1R"** who writes for this brand. On another article the Person is named
"PageFly", after the page-builder app.

**Do:** set the author on all five to a real person's name, or to
`Celeste L'Amour` where no named author applies. Online Store → Blog posts →
[article] → Author.

## 5. The 9 unpublished drafts — leave them unpublished

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

All authored `5K20RB-1R`. They read as generic AI filler. They are drafts, so
they are not indexable and carry no current risk.

Publishing thin content on a domain that is *recovering* from a scaled-content
problem is the one thing that would slow the recovery. Leave them alone until
the index has settled and the manual-action question is answered.

## 6. What to publish instead

Do not refill the blog to hit a number — that is the habit that produced the
original problem.

Three genuinely useful pieces written from what this business actually knows
will outperform fifty imported ones:

- How the scrunch knit is constructed, and why it does not go sheer under load.
- How to choose between a compressive and an easy fit, mapped to real body
  measurements.
- What the fabric actually is, by composition and weight.

You already have the raw material: `/pages/celeste-lamour` ("Fabric Engineer
Exposes the Legging Flaw") is that argument in advertorial form. Its
`bodySummary` currently begins with raw CSS (`.cl-sidebar-wrap { position:
fixed; …`), which means the page is leading with stylesheet text — worth fixing
on its own.

---

## Where this sits in the sequence

The blog was the worst thing on the domain. It is now largely handled, which
promotes **`worklist-competitor-products.md`** — 170 live product pages
declaring `"brand": "Gymshark"` — to the top of the list. Do that next.
