#!/usr/bin/env python3
"""Turn saved B-Stock / Superior Wireless auction pages into a priced spreadsheet.

Usage:
    python3 scripts/parse_bstock_page.py page1.html [page2.html ...] -o iPhone_Lot_Pricing

Reads the saved "Cell Phones" listing HTML, pulls one row per auction lot, and
writes an .xlsx (with live formulas) plus a .csv.

Each lot title follows:
    Apple <MODEL>[, <STORAGE>], <CARRIER>, <N> Units, Grade <G>, <CITY>, <STATE>
so the title is parsed right-to-left -- the model is whatever is left over, which
keeps multi-model lots ("iPhone XR, iPhone SE (2020) & More") intact.

Pricing: Total Excl. Shipping = Bulk Price x (1 + FEE_RATE); FEE_RATE lives in the
workbook's Assumptions!B4 so the sheet recalculates if the rate changes.
"""
import argparse, csv, html, json, re, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

FEE_RATE = 0.02
CARRIERS = {'T-Mobile', 'AT&T', 'Verizon', 'Sprint', 'Metro', 'Generic', 'Mixed Carrier', 'Unlocked'}


def parse_page(path):
    """Extract raw fields from every auction tile on one saved listing page."""
    h = open(path, encoding='utf-8', errors='replace').read()
    tiles = [t for t in re.split(r'(?=<li id="auction-\d+">)', h) if t.startswith('<li id="auction-')]
    out = []
    for t in tiles:
        aid = re.search(r'<li id="auction-(\d+)">', t).group(1)
        m = re.search(r'<div class="product-name">\s*<a href="([^"]+)">(.*?)</a>', t, re.S)
        bid = re.search(r'class="current_bid"[^>]*>.*?<strong>\s*\$([\d,]+(?:\.\d+)?)\s*</strong>', t, re.S)
        cpu = re.search(r'class="cost_per_unit">.*?<strong>\s*\$([\d,]+(?:\.\d+)?)\s*</strong>', t, re.S)
        bids = re.search(r'id="bid_number\d+">(\d+)<', t)
        closes = re.search(r'class="countdown">([^<]*)<', t)
        qty = re.search(r"'quantity':\s*(\d+)", t)
        out.append(dict(
            auction_id=aid, url=m.group(1), title=re.sub(r'\s+', ' ', m.group(2)).strip(),
            bulk=float(bid.group(1).replace(',', '')) if bid else None,
            listed_cpu=float(cpu.group(1).replace(',', '')) if cpu else None,
            bids=int(bids.group(1)) if bids else None,
            closes=closes.group(1).strip() if closes else '',
            qty=int(qty.group(1)) if qty else None))
    return out


def split_title(raw):
    """Parse a lot title right-to-left into its component fields."""
    t = html.unescape(raw).strip().rstrip(',').strip()
    if not t.startswith('Apple '):
        raise ValueError('unexpected title: ' + t)
    parts = [p.strip() for p in t[len('Apple '):].split(',')]
    state, city = parts.pop(), parts.pop()
    grade_tok, units_tok, carrier = parts.pop(), parts.pop(), parts.pop()

    if not grade_tok.startswith('Grade'):
        raise ValueError('no grade in: ' + t)
    grade = grade_tok[len('Grade'):].strip()
    handset_only = 'Handset Only' in grade
    grade = grade.split(' - ')[0].strip()

    mu = re.fullmatch(r'(\d+)\s+Units?', units_tok)
    if not mu:
        raise ValueError('no unit count in: ' + t)

    storage = ''
    if parts and re.fullmatch(r'\d+\s*(GB|TB)', parts[-1], re.I):
        storage = parts.pop().upper().replace(' ', '')

    return dict(model=', '.join(parts), storage=storage or 'Mixed / Not specified',
                carrier=carrier, grade=grade, handset_only='Yes' if handset_only else 'No',
                units=int(mu.group(1)), location=f'{city}, {state}', title=t)


def enrich(raw_rows):
    """Merge parsed titles with prices and derive the fee/total/per-unit figures."""
    rows = []
    for r in raw_rows:
        o = split_title(r['title'])
        o.update(auction_id=r['auction_id'], url=r['url'], bulk=r['bulk'],
                 listed_cpu=r['listed_cpu'], bids=r['bids'], closes=r['closes'])
        o['fee'] = round(o['bulk'] * FEE_RATE, 2)
        o['total'] = round(o['bulk'] * (1 + FEE_RATE), 2)
        o['cpu'] = round(o['total'] / o['units'], 2)

        # The page prints its own avg cost per unit; it must equal bulk / units.
        if o['carrier'] not in CARRIERS:
            print(f"  warn: unrecognized carrier {o['carrier']!r} in {o['title']}", file=sys.stderr)
        if r['qty'] is not None and r['qty'] != o['units']:
            print(f"  warn: unit count {o['units']} != tracking quantity {r['qty']} ({o['auction_id']})", file=sys.stderr)
        if abs(o['listed_cpu'] - o['bulk'] / o['units']) > 0.02:
            print(f"  warn: listed $/unit {o['listed_cpu']} != bulk/units ({o['auction_id']})", file=sys.stderr)
        rows.append(o)
    return rows


TIER = {'Pro Max': 0, 'Pro': 1, 'Plus': 2, '': 3, 'Mini': 4, 'e': 5}
STORAGE_GB = {'64GB': 64, '128GB': 128, '256GB': 256, '512GB': 512, '1TB': 1024}


def sort_key(o):
    """Newest generation first, then Pro Max -> e, then largest storage, then grade."""
    m = o['model']
    g = re.search(r'iPhone (\d+)', m)
    gen = int(g.group(1)) if g else -1          # SE / XR-only lots have no number
    mixed = 1 if ('&' in m or ',' in m) else 0  # multi-model lots sort to the bottom
    tier = 6
    for t, v in TIER.items():
        if t and m.endswith(' ' + t):
            tier = v
            break
    else:
        if re.fullmatch(r'iPhone \d+e', m):
            tier = 5
        elif re.fullmatch(r'iPhone \d+', m):
            tier = 3
    return (mixed, -gen, tier, -STORAGE_GB.get(o['storage'], 0), o['grade'])



def write_workbook(rows, out_base):
    ARIAL = 'Arial'
    HDR_FILL = PatternFill('solid', fgColor='1F3864')
    HDR_FONT = Font(name=ARIAL, bold=True, color='FFFFFF', size=10)
    IN_FONT  = Font(name=ARIAL, color='0000FF', size=10)
    YELLOW   = PatternFill('solid', fgColor='FFFF00')
    BAND     = PatternFill('solid', fgColor='F2F5FA')
    TOT_FILL = PatternFill('solid', fgColor='DDE3EF')
    thin = Side(style='thin', color='BFBFBF')
    BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

    wb = Workbook()

    # ---------------- Assumptions ----------------
    a = wb.active; a.title = 'Assumptions'
    a['A1'] = 'Superior Wireless Auctions (B-Stock) — iPhone Lot Pricing'
    a['A1'].font = Font(name=ARIAL, bold=True, size=14, color='1F3864')
    notes = [
        ('A3', 'INPUT — edit this cell', None),
        ('A4', 'Buyer fee / premium applied to bulk price', FEE_RATE),
    ]
    a['A3'].font = Font(name=ARIAL, bold=True, size=10)
    a['A4'].font = Font(name=ARIAL, size=10)
    a['B4'] = FEE_RATE
    a['B4'].font = IN_FONT; a['B4'].fill = YELLOW; a['B4'].border = BOX
    a['B4'].number_format = '0.0%'
    a['C4'] = '<-- Blue text on yellow = the only cell you edit. All totals recalculate from it.'
    a['C4'].font = Font(name=ARIAL, italic=True, size=9, color='808080')

    doc = [
        '',
        'HOW THE NUMBERS ARE BUILT',
        "    Bulk Price          = the lot's Current bid on the auction page (what the lot costs at that bid).",
        '    Fee @ 2%            = Bulk Price x 2%.',
        '    Total Excl. Shipping = Bulk Price + Fee. Excludes shipping, tax, and any other charges.',
        '    Cost Per Unit       = Total Excl. Shipping / Units.',
        '',
        'ASSUMPTIONS AND CAVEATS',
        '    1. "Multiply bulk price by 2%" is read as a 2% buyer fee ADDED to the bulk price.',
        '       The standalone 2% amount is also shown in its own column if you meant the fee alone.',
        '    2. Source page shows lots 1-96 of 208 (page 1 of 3). Pages 2 and 3 are NOT in this file.',
        '    3. These are LIVE auctions. Current bid rises with each new bid, so every price here is a',
        '       snapshot from the saved page, not a settled cost.',
        '    4. Shipping is excluded, per request. B-Stock lots ship from Dallas, TX.',
        '    5. Grade is taken verbatim from the lot title (New, A, A/B, B, B/C, C).',
        '    6. Lots titled "Mixed Carrier" or with no storage in the title are marked',
        '       "Mixed / Not specified" — open the auction link for the manifest.',
        '',
        'SOURCE',
        '    Superior Wireless Auction - Smartphone Liquidation | B-Stock',
        '    https://bstock.com/superior/cell-phones/?limit=96',
        '    Saved page supplied by user; captured 2026-08-02.',
    ]
    r = 6
    for line in doc:
        a.cell(row=r, column=1, value=line)
        c = a.cell(row=r, column=1)
        if line and not line.startswith(' '):
            c.font = Font(name=ARIAL, bold=True, size=10, color='1F3864')
        else:
            c.font = Font(name=ARIAL, size=10)
        r += 1
    a.column_dimensions['A'].width = 46
    a.column_dimensions['B'].width = 12
    a.column_dimensions['C'].width = 70

    # ---------------- Auction Inventory ----------------
    s = wb.create_sheet('Auction Inventory')
    cols = [
        ('Auction ID', 11), ('iPhone Model', 22), ('Storage', 20), ('Grade', 8),
        ('Units', 9), ('Carrier', 14), ('Handset Only', 13),
        ('Bulk Price (Current Bid)', 20), ('Site Avg $/Unit', 15),
        ('Fee @ 2%', 12), ('Total Excl. Shipping', 19), ('Cost Per Unit', 14),
        ('Bids', 7), ('Closes In', 11), ('Location', 13), ('Auction Link', 46),
    ]
    for i, (h, w) in enumerate(cols, 1):
        c = s.cell(row=1, column=i, value=h)
        c.font = HDR_FONT; c.fill = HDR_FILL; c.border = BOX
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        s.column_dimensions[get_column_letter(i)].width = w
    s.row_dimensions[1].height = 30

    for n, o in enumerate(rows):
        r = n + 2
        vals = [int(o['auction_id']), o['model'], o['storage'], o['grade'], o['units'],
                o['carrier'], o['handset_only'], o['bulk'], o['listed_cpu'],
                f'=H{r}*Assumptions!$B$4', f'=H{r}+J{r}', f'=IF(E{r}=0,"",K{r}/E{r})',
                o['bids'], o['closes'], o['location'], o['url']]
        for i, v in enumerate(vals, 1):
            c = s.cell(row=r, column=i, value=v)
            c.font = Font(name=ARIAL, size=10)
            c.border = BOX
            if n % 2: c.fill = BAND
        s.cell(row=r, column=16).font = Font(name=ARIAL, size=9, color='0563C1', underline='single')
        s.cell(row=r, column=16).hyperlink = o['url']
        for col in (8, 11):
            s.cell(row=r, column=col).number_format = '$#,##0.00'
        for col in (9, 10, 12):
            s.cell(row=r, column=col).number_format = '$#,##0.00'
        s.cell(row=r, column=5).number_format = '#,##0'
        for col in (1, 4, 5, 7, 13, 14):
            s.cell(row=r, column=col).alignment = Alignment(horizontal='center')

    last = len(rows) + 1
    t = last + 1
    s.cell(row=t, column=1, value='TOTAL / BLENDED')
    s.merge_cells(start_row=t, start_column=1, end_row=t, end_column=4)
    for col, f in [(5, f'=SUM(E2:E{last})'), (8, f'=SUM(H2:H{last})'),
                   (10, f'=SUM(J2:J{last})'), (11, f'=SUM(K2:K{last})'),
                   (12, f'=IF(E{t}=0,"",K{t}/E{t})')]:
        s.cell(row=t, column=col, value=f)
    for i in range(1, 17):
        c = s.cell(row=t, column=i)
        c.font = Font(name=ARIAL, bold=True, size=10); c.fill = TOT_FILL; c.border = BOX
    s.cell(row=t, column=5).number_format = '#,##0'
    for col in (8, 10, 11, 12):
        s.cell(row=t, column=col).number_format = '$#,##0.00'
    s.cell(row=t, column=1).alignment = Alignment(horizontal='left')
    s.cell(row=t, column=13, value='<- blended cost per unit across all lots on this page')
    s.cell(row=t, column=13).font = Font(name=ARIAL, italic=True, size=9, color='808080')
    s.merge_cells(start_row=t, start_column=13, end_row=t, end_column=16)

    s.freeze_panes = 'B2'
    s.auto_filter.ref = f'A1:P{last}'

    # ---------------- Rollup sheets ----------------
    def rollup(name, field, idx, order=None):
        sh = wb.create_sheet(name)
        # Tiebreak on the label itself: set iteration order varies per process, so
        # two keys that rank equally would otherwise swap rows between runs.
        uniq = {o[field] for o in rows}
        keys = sorted(uniq, key=lambda k: (order(k), k)) if order else sorted(uniq)
        hd = [(name.split(' by ')[1], 24), ('Lots', 8), ('Units', 10),
              ('Bulk Price Total', 18), ('Fee @ 2%', 14), ('Total Excl. Shipping', 19),
              ('Blended Cost Per Unit', 20)]
        for i, (h, w) in enumerate(hd, 1):
            c = sh.cell(row=1, column=i, value=h)
            c.font = HDR_FONT; c.fill = HDR_FILL; c.border = BOX
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            sh.column_dimensions[get_column_letter(i)].width = w
        sh.row_dimensions[1].height = 30
        col = get_column_letter(idx)
        rng = f"'Auction Inventory'!${col}$2:${col}${last}"
        for n, k in enumerate(keys):
            r = n + 2
            sh.cell(row=r, column=1, value=k)
            sh.cell(row=r, column=2, value=f'=COUNTIF({rng},$A{r})')
            sh.cell(row=r, column=3, value=f"=SUMIF({rng},$A{r},'Auction Inventory'!$E$2:$E${last})")
            sh.cell(row=r, column=4, value=f"=SUMIF({rng},$A{r},'Auction Inventory'!$H$2:$H${last})")
            sh.cell(row=r, column=5, value=f'=D{r}*Assumptions!$B$4')
            sh.cell(row=r, column=6, value=f'=D{r}+E{r}')
            sh.cell(row=r, column=7, value=f'=IF(C{r}=0,"",F{r}/C{r})')
            for i in range(1, 8):
                c = sh.cell(row=r, column=i)
                c.font = Font(name=ARIAL, size=10); c.border = BOX
                if n % 2: c.fill = BAND
            sh.cell(row=r, column=3).number_format = '#,##0'
            for i in (4, 5, 6, 7):
                sh.cell(row=r, column=i).number_format = '$#,##0.00'
            sh.cell(row=r, column=2).alignment = Alignment(horizontal='center')
        tr = len(keys) + 2
        sh.cell(row=tr, column=1, value='TOTAL / BLENDED')
        for i, f in [(2, f'=SUM(B2:B{tr-1})'), (3, f'=SUM(C2:C{tr-1})'), (4, f'=SUM(D2:D{tr-1})'),
                     (5, f'=SUM(E2:E{tr-1})'), (6, f'=SUM(F2:F{tr-1})'),
                     (7, f'=IF(C{tr}=0,"",F{tr}/C{tr})')]:
            sh.cell(row=tr, column=i, value=f)
        for i in range(1, 8):
            c = sh.cell(row=tr, column=i)
            c.font = Font(name=ARIAL, bold=True, size=10); c.fill = TOT_FILL; c.border = BOX
        sh.cell(row=tr, column=3).number_format = '#,##0'
        for i in (4, 5, 6, 7):
            sh.cell(row=tr, column=i).number_format = '$#,##0.00'
        sh.freeze_panes = 'A2'

    rollup('Summary by Model', 'model', 2,
            order=lambda m: sort_key({'model': m, 'storage': '', 'grade': ''}))
    rollup('Summary by Grade', 'grade', 4)
    rollup('Summary by Storage', 'storage', 3)
    wb.save(out_base + '.xlsx')


CSV_COLS = ['auction_id', 'model', 'storage', 'grade', 'units', 'carrier', 'handset_only',
            'bulk', 'listed_cpu', 'fee', 'total', 'cpu', 'bids', 'closes', 'location', 'url']
CSV_HDR = ['Auction ID', 'iPhone Model', 'Storage', 'Grade', 'Units', 'Carrier', 'Handset Only',
           'Bulk Price (Current Bid)', 'Site Avg $/Unit', 'Fee @ 2%', 'Total Excl. Shipping',
           'Cost Per Unit', 'Bids', 'Closes In', 'Location', 'Auction Link']


def write_csv(rows, out_base):
    with open(out_base + '.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(CSV_HDR)
        for o in rows:
            w.writerow([o[c] for c in CSV_COLS])
        tu = sum(o['units'] for o in rows)
        tb = sum(o['bulk'] for o in rows)
        w.writerow(['TOTAL', '', '', '', tu, '', '', round(tb, 2), '', round(tb * FEE_RATE, 2),
                    round(tb * (1 + FEE_RATE), 2), round(tb * (1 + FEE_RATE) / tu, 2), '', '', '', ''])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pages', nargs='+', help='saved listing page(s), e.g. page1.html page2.html')
    ap.add_argument('-o', '--out', default='iPhone_Lot_Pricing', help='output basename')
    args = ap.parse_args()

    raw = []
    for p in args.pages:
        got = parse_page(p)
        print(f'{p}: {len(got)} lots')
        raw.extend(got)

    seen, rows = set(), []
    for o in enrich(raw):
        if o['auction_id'] in seen:       # same lot can appear on two saved pages
            continue
        seen.add(o['auction_id'])
        rows.append(o)
    rows.sort(key=sort_key)

    write_workbook(rows, args.out)
    write_csv(rows, args.out)
    tu = sum(o['units'] for o in rows)
    tb = sum(o['bulk'] for o in rows)
    print(f'{len(rows)} lots | {tu:,} units | bulk ${tb:,.2f} | '
          f'total ${tb * (1 + FEE_RATE):,.2f} | blended ${tb * (1 + FEE_RATE) / tu:,.2f}/unit')
    print(f'wrote {args.out}.xlsx and {args.out}.csv')
    print('NOTE: run scripts/recalc.py (LibreOffice) to cache formula values before sharing.')


if __name__ == '__main__':
    main()
