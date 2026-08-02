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

---

# Auction vs Amazon comparison

`auction-vs-amazon.csv` prices all 93 iPhone lots from the Superior Wireless
Auctions (B-Stock) listing against the Amazon Renewed comps above, matched on
model + capacity + condition grade.

`lot-ledger.html` is the interactive version — filter by lock status, bulk size,
or profitability; sort by unit profit, lot profit, margin, or capital required.

## Grade mapping

| B-Stock | Amazon Renewed |
| --- | --- |
| Grade A | Refurbished - Excellent |
| Grade B | Refurbished - Good |
| Grade C | Refurbished - Acceptable |

Grade-matched pricing matters: Amazon's discount from Excellent to Acceptable
ranged from 4% (iPhone 14 Pro Max) to 21% (iPhone 13) across the 23 listings.
Using the headline Excellent price for a Grade C lot overstates margin
substantially.

## Cost model

Editable at the top of the generating script. Defaults:

| Input | Value |
| --- | --- |
| Amazon referral fee | 8% |
| Fulfilment per unit | $6.00 |
| Test / wipe / accessories / packaging | $12.00 |
| Inbound freight per unit | $6.00 |
| Returns + defect allowance | 8% of revenue |
| Locked-resale haircut (sensitivity) | 20% |

Not modelled: B-Stock buyer's premium, carrier unlock cost, storage, or cost of
capital while inventory sells.

## The carrier problem

Every Amazon comp is carrier-unlocked. 27 of the 34 lots that clear a profit at
current bids are T-Mobile or AT&T locked, so they cannot reach the comp price
unless they can be unlocked. The `net_if_locked` columns show each lot's result
if it has to sell locked at a 20% discount — six lots flip to a loss.

## Coverage

56 of 93 lots have no comp in the Amazon page-1 set: the iPhone 17 family,
13 Pro Max, 11 Pro / 11 Pro Max, and every 512GB/1TB capacity. Those rows carry
cost data only and are unpriced, not unprofitable.

Unit cost is current bid ÷ units with roughly a day left on the clock, so every
figure is a floor.
