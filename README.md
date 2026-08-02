# Amazon Renewed iPhones — Search Page 1

Extracted from the Amazon search listing for **Renewed Smartphones → Apple**
(`s?i=mobile&rh=n:2335752011,n:7072561011,p_123:110955`), captured 2026-08-02.

Page 1 shows **24 tiles out of 114 results**. 23 are iPhones; tile 14 is an
accessory (Apple iPhone FineWoven Wallet with MagSafe, `B0FQFQ1L35`) and is
excluded from the dataset.

## Files

- `iphone-page1.csv` — one row per iPhone, in on-page order.

## Columns

| Column | Notes |
| --- | --- |
| `position` | Order on page 1, accessory removed (so 1–23, not 1–24) |
| `asin` | Amazon ASIN |
| `model` | Parsed from the listing title |
| `storage` | Buy-box storage. Most listings also sell other capacities under the same ASIN |
| `carrier_lock` | Every listing is carrier-unlocked; wording follows the listing |
| `grades_available` | Condition grades sold on the product page |
| `default_grade` | Grade pre-selected in the buy box, and the one the search-page price refers to |
| `price_usd` | Buy-box price at capture time |
| `rating`, `review_count` | Star rating and rounded review count from the search tile |

## Where the fields come from

Model, storage and lock status are in the listing title. Grade is **not** on the
search page — it lives on each product page, as a buying-options accordion with
one row per condition grade. Those rows were read directly from the page markup
(`.accordion-caption`) rather than inferred.

## Two things worth knowing about the grade field

**"Renewed" is the program, not the grade.** Every title ends in `(Renewed)`,
which only means the listing is part of Amazon Renewed. The actual grade is one
of `Refurbished - Excellent` / `Good` / `Acceptable`, chosen on the product page.

**"Renewed Premium" is not a grade you can pick here.** The phrase appears on
these pages only inside the Amazon Renewed Guarantee boilerplate ("...or within
365 days of receipt of a Renewed Premium or Renewed Automotive product"). No
listing on page 1 offers it as a selectable option.

## Caveats

Prices, stock and available grades change frequently; treat the price and
`grades_available` columns as a snapshot. Grades reflect which offers existed at
capture time, so a listing showing only Excellent/Good may show Acceptable later
if a seller lists one.
