# iPhone pricing datasets

Two snapshots of iPhone pricing from different sides of the market — wholesale
liquidation lots, and retail refurbished listings.

| Dataset | Source | Files |
| --- | --- | --- |
| [Superior Wireless auction lots](#superior-wireless-auctions--iphone-lot-pricing) | B-Stock liquidation auctions | `iPhone_Lot_Pricing.xlsx`, `iPhone_Lot_Pricing.csv` |
| [Amazon Renewed iPhones](#amazon-renewed-iphones--search-page-1) | Amazon search page 1 | `iphone-page1.csv` |

---

# Superior Wireless Auctions — iPhone Lot Pricing

Priced breakdown of the iPhone lots listed on the Superior Wireless Auctions
(B-Stock) smartphone liquidation marketplace.

| File | What it is |
|---|---|
| `iPhone_Lot_Pricing.xlsx` | The spreadsheet — 96 lots, live formulas, 3 rollup tabs |
| `iPhone_Lot_Pricing.csv` | Same rows, flat, for import elsewhere |
| `scripts/parse_bstock_page.py` | Regenerates both from saved listing pages |
| `scripts/recalc.py` | Caches formula values via LibreOffice before sharing |

## The pricing math

```
Fee @ 2%             = Bulk Price × 2%
Total Excl. Shipping = Bulk Price + Fee
Cost Per Unit        = Total Excl. Shipping ÷ Units
```

"Bulk Price" is the lot's **Current bid** on the auction page. The 2% rate lives in
`Assumptions!B4` — change that one cell and every figure in the workbook recalculates.

The standalone 2% amount also gets its own column, in case the intent was the fee
alone rather than a fee added on top.

## Tabs

- **Assumptions** — the editable rate, plus the full caveat list and source
- **Auction Inventory** — one row per lot: model, storage, grade, units, carrier,
  bulk price, fee, total, cost per unit, bids, closing time, link
- **Summary by Model / Grade / Storage** — lots, units, spend and blended cost per unit

## Caveats

1. The source page covers lots **1–96 of 208** (page 1 of 3). Pages 2 and 3 are not included.
2. These are **live auctions** — the current bid rises with each new bid, so every
   price is a snapshot, not a settled cost.
3. Shipping, tax and any other charges are excluded. Lots ship from Dallas, TX.
4. Grade is verbatim from the lot title (`New`, `A`, `A/B`, `B`, `B/C`, `C`).
5. Lots titled "Mixed Carrier", or with no storage in the title, show
   `Mixed / Not specified` — open the auction link for the manifest.

## Regenerating

Save the listing page from a browser (**Save as → Webpage, Complete**), then:

```bash
python3 scripts/parse_bstock_page.py page1.html page2.html page3.html -o iPhone_Lot_Pricing
python3 scripts/recalc.py iPhone_Lot_Pricing.xlsx 300
```

Passing several pages at once de-duplicates by auction ID, so overlapping saves are safe.
The parser warns on stderr if a lot's unit count, carrier, or per-unit price fails its
cross-check rather than silently writing a bad row.

`recalc.py` needs LibreOffice Calc (`apt-get install -y libreoffice-calc`). Without it
the formulas are still correct, but cells read as blank in previewers that show cached
values instead of recalculating.

---

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
