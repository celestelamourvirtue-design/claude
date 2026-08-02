#!/usr/bin/env python3
"""Build the full workbook: auction lot pricing + resale profit potential.

    python3 scripts/build_profit_model.py auction.html --ebay ebay1.html ebay2.html \
        -o iPhone_Lot_Pricing

Adds three tabs to the base auction workbook:
  Profit Potential  one row per lot, with eBay and instant-cashout min/max and the
                    profit that falls out of each after the lot's cost per unit
  eBay Comps        every sold listing that could be classified to a single config
  SellCell Cashout  the iPhone 17 Pro Max buyback grid read off the SellCell captures

Matching is strict on purpose: a comp is only used when its model AND storage match
the lot exactly and its condition is a fair stand-in for the lot's grade. Anything
that cannot be pinned to one configuration (multi-variant listings with a price
range) is dropped rather than averaged in.
"""
import argparse, collections, json, re, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_bstock_page as base
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------- eBay parsing
MODELS = ['iPhone 17 Pro Max','iPhone 17 Pro','iPhone 17 Air','iPhone Air','iPhone 17',
          'iPhone 16 Pro Max','iPhone 16 Pro','iPhone 16 Plus','iPhone 16e','iPhone 16',
          'iPhone 15 Pro Max','iPhone 15 Pro','iPhone 15 Plus','iPhone 15',
          'iPhone 14 Pro Max','iPhone 14 Pro','iPhone 14 Plus','iPhone 14',
          'iPhone 13 Pro Max','iPhone 13 Pro','iPhone 13 Mini','iPhone 13 mini','iPhone 13',
          'iPhone 12 Pro Max','iPhone 12 Pro','iPhone 12 Mini','iPhone 12 mini','iPhone 12',
          'iPhone 11 Pro Max','iPhone 11 Pro','iPhone 11',
          'iPhone SE (2022)','iPhone SE 2022','iPhone SE (2020)','iPhone SE 2020','iPhone SE',
          'iPhone XS Max','iPhone XS','iPhone XR','iPhone X']
VALID_STORAGE = {'64GB','128GB','256GB','512GB','1TB','2TB'}

# eBay condition -> the B-Stock grade band it stands in for.
# "Pre-Owned" carries no grade signal, so it gets its own 'Used' band.
COND_CLASS = {'Brand New':'New','New (Other)':'New','Open Box':'New',
              'Excellent - Refurbished':'A','Very Good - Refurbished':'B',
              'Good - Refurbished':'C','Pre-Owned':'Used',
              'For parts or not working':'Parts','Parts Only':'Parts'}

# Which bands are acceptable comps for each lot grade. 'Used' is compatible with
# any used grade but never with Grade New.
GRADE_OK = {'New':{'New'}, 'A':{'A','Used'}, 'A/B':{'A','B','Used'},
            'B':{'B','Used'}, 'B/C':{'B','C','Used'}, 'C':{'C','Used'}}

CARRIER_LOCKED = {'T-Mobile','AT&T','Verizon','Sprint','Metro'}


def find_model(s):
    for m in MODELS:
        if re.search(r'\b' + re.escape(m).replace(r'\ ', r'\s+') + r'\b', s, re.I):
            n = m.replace('mini','Mini').replace('SE 2022','SE (2022)').replace('SE 2020','SE (2020)')
            return 'iPhone Air' if n == 'iPhone 17 Air' else n
    return ''


def find_storage(s):
    m = re.search(r'\b(\d+)\s*(GB|TB|MB|KB)\b', s, re.I)
    if not m: return ''
    v = f'{m.group(1)}{m.group(2).upper()}'
    return v if v in VALID_STORAGE else ''


def find_lock(s):
    t = s.lower()
    if re.search(r'\b(factory\s+)?unlocked\b|\bsim[\s-]?free\b', t): return 'Unlocked'
    for c, n in [('at&t','AT&T'),('t-mobile','T-Mobile'),('verizon','Verizon'),('sprint','Sprint'),
                 ('metro','Metro'),('xfinity','Xfinity'),('spectrum','Spectrum'),
                 ('u.s. cellular','US Cellular'),('straight talk','Straight Talk'),
                 ('boost','Boost'),('simple mobile','Simple Mobile'),('cricket','Cricket')]:
        if c in t: return n
    return ''


def parse_ebay(paths):
    """One row per sold listing that resolves to a single model/storage/condition."""
    kept, dropped = [], collections.Counter()
    for p in paths:
        soup = BeautifulSoup(open(p, encoding='utf-8', errors='replace'), 'lxml')
        for c in soup.select('li.s-card'):
            t = c.select_one('.s-card__title')
            title = t.get_text(' ', strip=True).replace('Opens in a new window or tab', '').strip() if t else ''
            if not title or title == 'Shop on eBay':
                continue
            sub = c.select_one('.s-card__subtitle')
            sub = sub.get_text(' ', strip=True) if sub else ''
            attrs = [a.get_text(' ', strip=True) for a in c.select('.s-card__attribute-row')]
            praw = next((a for a in attrs if a.startswith('$')), '')
            cap = c.select_one('.s-card__caption')

            parts = [x.strip() for x in sub.split('·')]
            cond = parts[0] if parts else ''
            model = (find_model(parts[1]) if len(parts) > 1 else '') or find_model(title)
            storage = (find_storage(parts[2]) if len(parts) > 2 else '') or find_storage(title)
            lock = (parts[3] if len(parts) > 3 else '') or find_lock(title)
            lock = 'Unlocked' if lock in ('Factory Unlocked', 'Gsm Unlocked') else lock
            nums = [float(x.replace(',', '')) for x in re.findall(r'\$([\d,]+\.\d\d)', praw)]
            band = COND_CLASS.get(cond, '')

            if not model:            dropped['no model'] += 1; continue
            if not storage:          dropped['no / implausible storage'] += 1; continue
            if not band:             dropped['unmapped condition'] += 1; continue
            if not nums:             dropped['no price'] += 1; continue
            if ' to ' in praw:       dropped['multi-variant price range'] += 1; continue

            kept.append(dict(model=model, storage=storage, lock=lock or 'Not stated',
                             condition=cond, grade_band=band, price=nums[0], title=title,
                             sold=cap.get_text(' ', strip=True).replace('Sold', '').strip() if cap else ''))
    return kept, dropped


# ------------------------------------------------- SellCell (read from captures)
# NETWORK = Unlocked on every capture; capacity and condition are what vary.
SELLCELL = {
 ('256GB','MINT'):   [943,942,942,938,935,925,925,925,921,921,903,818,800,780],
 ('256GB','GOOD'):   [885,875,870,870,867,865,860,860,801,800,741,738,720,700],
 ('256GB','POOR'):   [770,765,720,707,651,531,531,522,522,516,502,330,285],
 ('256GB','FAULTY'): [561,361,361,360,350,332,330,261,261,258,95,85],
 ('512GB','MINT'):   [1039,1038,1037,1035,1034,1025,1025,1025,1021,1021,1008,935,880,876],
 ('512GB','GOOD'):   [985,975,970,970,965,962,960,960,883,882,857,814,788.40,785],
 ('512GB','POOR'):   [870,865,794,723,721,593,593,582,582,576,505,380,295],
 ('512GB','FAULTY'): [721,391,391,390,380,380,372,291,291,288,109,90],
 ('1TB','MINT'):     [1101,1101,1100,1099,1096,1090,1090,1090,1086,1086,1076,988,950],
 ('1TB','GOOD'):     [1050,1040,1035,1035,1030,1025,1025,1024,935,935,933,875,869],
 ('1TB','POOR'):     [935,930,842,832,767,633,633,621,621,615,555,430,305],
 ('1TB','FAULTY'):   [831,437,436,435,433,430,420,311,311,308,121,90],
}
SELLCELL_MODEL = 'iPhone 17 Pro Max'
GRADE_TO_SELLCELL = {'New':'MINT','A':'GOOD','A/B':'GOOD','B':'GOOD','B/C':'POOR','C':'POOR'}


def match(lots, comps):
    by_cfg = collections.defaultdict(list)
    for c in comps:
        by_cfg[(c['model'], c['storage'])].append(c)

    out = []
    for l in lots:
        r = dict(l)
        ok = GRADE_OK.get(l['grade'], set())
        m = [c for c in by_cfg.get((l['model'], l['storage']), []) if c['grade_band'] in ok]
        r['ebay_n'] = len(m)
        if m:
            px = sorted(c['price'] for c in m)
            r['ebay_lo'], r['ebay_hi'] = px[0], px[-1]
            r['ebay_med'] = round(statistics.median(px), 2)
            lk = collections.Counter(c['lock'] for c in m)
            r['comp_locks'] = ', '.join(f'{v} {k}' for k, v in lk.most_common(3))
            r['comp_conds'] = ', '.join(f'{v} {k}' for k, v in
                                        collections.Counter(c['condition'] for c in m).most_common(3))
            r['warn'] = ('Lot is %s-locked, comps mostly Unlocked - expect a discount'
                         % l['carrier']) if (l['carrier'] in CARRIER_LOCKED
                                             and lk.get('Unlocked', 0) > lk.get(l['carrier'], 0)) else ''
            if r['ebay_n'] < 3:
                r['warn'] = (r['warn'] + ' | ' if r['warn'] else '') + 'Thin: %d comp(s)' % r['ebay_n']
        else:
            r['ebay_lo'] = r['ebay_hi'] = r['ebay_med'] = None
            r['comp_locks'] = r['comp_conds'] = ''
            r['warn'] = 'No comp on this page set for this model + storage'

        cond = GRADE_TO_SELLCELL.get(l['grade'], '')
        v = SELLCELL.get((l['storage'], cond)) if l['model'] == SELLCELL_MODEL else None
        if v:
            r['sc_cond'], r['sc_n'] = cond, len(v)
            r['sc_lo'], r['sc_hi'] = min(v), max(v)
        else:
            r['sc_cond'] = r['sc_n'] = r['sc_lo'] = r['sc_hi'] = None
        out.append(r)
    return out


# ------------------------------------------------------------------- workbook
ARIAL = 'Arial'
HDR_FILL = PatternFill('solid', fgColor='1F3864')
GRN_FILL = PatternFill('solid', fgColor='2E6B4F')
AMB_FILL = PatternFill('solid', fgColor='7A5B1E')
HDR_FONT = Font(name=ARIAL, bold=True, color='FFFFFF', size=10)
BAND = PatternFill('solid', fgColor='F2F5FA')
TOT_FILL = PatternFill('solid', fgColor='DDE3EF')
YELLOW = PatternFill('solid', fgColor='FFFF00')
thin = Side(style='thin', color='BFBFBF')
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
MONEY = '$#,##0.00'
PROFIT_FMT = '$#,##0.00;[Red]($#,##0.00);-'


def hdr(sh, cols, fills=None):
    for i, (h, w) in enumerate(cols, 1):
        c = sh.cell(row=1, column=i, value=h)
        c.font = HDR_FONT
        c.fill = (fills or {}).get(i, HDR_FILL)
        c.border = BOX
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        sh.column_dimensions[get_column_letter(i)].width = w
    sh.row_dimensions[1].height = 42


def build(rows, comps, out_base):
    base.write_workbook(rows, out_base)          # auction tabs, formulas intact
    wb = load_workbook(out_base + '.xlsx')
    inv_last = len(rows) + 1

    # ---- Assumptions: add the eBay fee lever
    a = wb['Assumptions']
    a['A5'] = 'eBay selling fee applied to eBay resale prices'
    a['A5'].font = Font(name=ARIAL, size=10)
    a['B5'] = 0.0
    a['B5'].font = Font(name=ARIAL, color='0000FF', size=10)
    a['B5'].fill = YELLOW; a['B5'].border = BOX; a['B5'].number_format = '0.0%'
    a['C5'] = '<-- 0% = gross resale, as requested. Set to ~13% to model real eBay fees.'
    a['C5'].font = Font(name=ARIAL, italic=True, size=9, color='808080')

    # ---- Profit Potential
    p = wb.create_sheet('Profit Potential', 2)
    cols = [('Auction ID',10),('iPhone Model',21),('Storage',19),('Grade',7),('Carrier',13),
            ('Units',8),('Cost Per Unit',13),
            ('eBay Comps (n)',10),('eBay Min',12),('eBay Median',12),('eBay Max',12),
            ('Cashout Cond',11),('Cashout Vendors (n)',11),('Cashout Min',12),('Cashout Max',12),
            ('Profit/Unit @ Cashout Min',14),('Profit/Unit @ Cashout Max',14),
            ('Profit/Unit @ eBay Min',14),('Profit/Unit @ eBay Max',14),
            ('Total @ Cashout Min',15),('Total @ Cashout Max',15),
            ('Total @ eBay Min',15),('Total @ eBay Max',15),
            ('Comp Conditions Used',30),('Comp Lock Mix',26),('Match Warning',44)]
    hdr(p, cols, fills={i: GRN_FILL for i in range(16, 24)} | {26: AMB_FILL})

    for n, r in enumerate(rows):
        i = n + 2
        p.cell(row=i, column=1, value=int(r['auction_id']))
        p.cell(row=i, column=2, value=r['model'])
        p.cell(row=i, column=3, value=r['storage'])
        p.cell(row=i, column=4, value=r['grade'])
        p.cell(row=i, column=5, value=r['carrier'])
        p.cell(row=i, column=6, value=r['units'])
        p.cell(row=i, column=7, value=f"='Auction Inventory'!L{i}")
        p.cell(row=i, column=8, value=r['ebay_n'] or None)
        p.cell(row=i, column=9, value=r['ebay_lo'])
        p.cell(row=i, column=10, value=r['ebay_med'])
        p.cell(row=i, column=11, value=r['ebay_hi'])
        p.cell(row=i, column=12, value=r['sc_cond'])
        p.cell(row=i, column=13, value=r['sc_n'])
        p.cell(row=i, column=14, value=r['sc_lo'])
        p.cell(row=i, column=15, value=r['sc_hi'])
        # Blank resale price -> blank profit, so "no data" never reads as "no profit".
        p.cell(row=i, column=16, value=f'=IF(N{i}="","",N{i}-$G{i})')
        p.cell(row=i, column=17, value=f'=IF(O{i}="","",O{i}-$G{i})')
        p.cell(row=i, column=18, value=f'=IF(I{i}="","",I{i}*(1-Assumptions!$B$5)-$G{i})')
        p.cell(row=i, column=19, value=f'=IF(K{i}="","",K{i}*(1-Assumptions!$B$5)-$G{i})')
        for src, dst in ((16, 20), (17, 21), (18, 22), (19, 23)):
            s = get_column_letter(src)
            p.cell(row=i, column=dst, value=f'=IF({s}{i}="","",{s}{i}*$F{i})')
        p.cell(row=i, column=24, value=r['comp_conds'])
        p.cell(row=i, column=25, value=r['comp_locks'])
        p.cell(row=i, column=26, value=r['warn'])

        for col in range(1, 27):
            c = p.cell(row=i, column=col)
            c.font = Font(name=ARIAL, size=10); c.border = BOX
            if n % 2: c.fill = BAND
        for col in (7, 9, 10, 11, 14, 15):
            p.cell(row=i, column=col).number_format = MONEY
        for col in range(16, 24):
            p.cell(row=i, column=col).number_format = PROFIT_FMT
        p.cell(row=i, column=6).number_format = '#,##0'
        for col in (1, 4, 6, 8, 12, 13):
            p.cell(row=i, column=col).alignment = Alignment(horizontal='center')
        p.cell(row=i, column=26).font = Font(name=ARIAL, size=9, color='9C5700')

    t = len(rows) + 2
    p.cell(row=t, column=1, value='TOTAL')
    p.merge_cells(start_row=t, start_column=1, end_row=t, end_column=5)
    p.cell(row=t, column=6, value=f'=SUM(F2:F{t-1})')
    for col in range(20, 24):
        L = get_column_letter(col)
        p.cell(row=t, column=col, value=f'=SUM({L}2:{L}{t-1})')
    for col in range(1, 27):
        c = p.cell(row=t, column=col)
        c.font = Font(name=ARIAL, bold=True, size=10); c.fill = TOT_FILL; c.border = BOX
    p.cell(row=t, column=6).number_format = '#,##0'
    for col in range(20, 24):
        p.cell(row=t, column=col).number_format = PROFIT_FMT
    p.cell(row=t, column=1).alignment = Alignment(horizontal='left')
    p.freeze_panes = 'G2'
    p.auto_filter.ref = f'A1:Z{t-1}'

    # ---- eBay Comps
    e = wb.create_sheet('eBay Comps')
    hdr(e, [('iPhone Model',21),('Storage',10),('Condition',22),('Grade Band',10),
            ('Lock',14),('Sold Price',12),('Sold Date',13),('Listing Title',80)])
    for n, c in enumerate(sorted(comps, key=lambda x: (base.sort_key(
            {'model': x['model'], 'storage': x['storage'], 'grade': ''}), x['price']))):
        i = n + 2
        for col, v in enumerate([c['model'], c['storage'], c['condition'], c['grade_band'],
                                 c['lock'], c['price'], c['sold'], c['title']], 1):
            cell = e.cell(row=i, column=col, value=v)
            cell.font = Font(name=ARIAL, size=10); cell.border = BOX
            if n % 2: cell.fill = BAND
        e.cell(row=i, column=6).number_format = MONEY
    e.freeze_panes = 'A2'
    e.auto_filter.ref = f'A1:H{len(comps)+1}'

    # ---- SellCell Cashout
    s = wb.create_sheet('SellCell Cashout')
    hdr(s, [('Model',21),('Network',12),('Capacity',11),('Condition',11),
            ('Vendors',9),('Lowest Offer',13),('Median Offer',13),('Highest Offer',13)])
    order = {'MINT':0,'GOOD':1,'POOR':2,'FAULTY':3}
    keys = sorted(SELLCELL, key=lambda k: (base.STORAGE_GB.get(k[0], 0), order[k[1]]))
    for n, k in enumerate(keys):
        v = sorted(SELLCELL[k]); i = n + 2
        vals = [SELLCELL_MODEL, 'Unlocked', k[0], k[1], len(v), v[0],
                round(statistics.median(v), 2), v[-1]]
        for col, val in enumerate(vals, 1):
            c = s.cell(row=i, column=col, value=val)
            c.font = Font(name=ARIAL, size=10); c.border = BOX
            if n % 2: c.fill = BAND
        for col in (6, 7, 8):
            s.cell(row=i, column=col).number_format = MONEY
        for col in (2, 3, 4, 5):
            s.cell(row=i, column=col).alignment = Alignment(horizontal='center')
    s.freeze_panes = 'A2'
    s.cell(row=len(keys)+3, column=1,
           value='Every capture had NETWORK = Unlocked. Capacity and condition are what vary. '
                 'Captured 2026-08-02 from sellcell.com/phones/apple/iphone-17-pro-max.')
    s.cell(row=len(keys)+3, column=1).font = Font(name=ARIAL, italic=True, size=9, color='808080')

    wb.save(out_base + '.xlsx')
    return inv_last


PROFIT_HDR = ['Auction ID','iPhone Model','Storage','Grade','Carrier','Units','Cost Per Unit',
              'eBay Comps (n)','eBay Min','eBay Median','eBay Max',
              'Cashout Cond','Cashout Vendors (n)','Cashout Min','Cashout Max',
              'Profit/Unit @ Cashout Min','Profit/Unit @ Cashout Max',
              'Profit/Unit @ eBay Min','Profit/Unit @ eBay Max',
              'Total @ Cashout Min','Total @ Cashout Max','Total @ eBay Min','Total @ eBay Max',
              'Comp Conditions Used','Comp Lock Mix','Match Warning']


def write_profit_csv(rows, out_base):
    """Flat mirror of the Profit Potential tab, values already resolved."""
    import csv

    with open(out_base + '_Profit.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(PROFIT_HDR)
        for r in rows:
            cpu = r['bulk'] * (1 + base.FEE_RATE) / r['units']
            # Round only on output. Rounding per-unit first and then multiplying
            # would drift by up to a cent per unit against the workbook's totals.
            raw = [None if r[k] is None else r[k] - cpu
                   for k in ('sc_lo', 'sc_hi', 'ebay_lo', 'ebay_hi')]
            per = ['' if x is None else round(x, 2) for x in raw]
            tot = ['' if x is None else round(x * r['units'], 2) for x in raw]
            w.writerow([r['auction_id'], r['model'], r['storage'], r['grade'], r['carrier'],
                        r['units'], round(cpu, 2), r['ebay_n'] or '', r['ebay_lo'] or '',
                        r['ebay_med'] or '', r['ebay_hi'] or '', r['sc_cond'] or '',
                        r['sc_n'] or '', r['sc_lo'] or '', r['sc_hi'] or '',
                        *per, *tot, r['comp_conds'], r['comp_locks'], r['warn']])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('auction', help='saved B-Stock listing page')
    ap.add_argument('--ebay', nargs='+', required=True, help='saved eBay sold-listing pages')
    ap.add_argument('-o', '--out', default='iPhone_Lot_Pricing')
    args = ap.parse_args()

    lots = base.enrich(base.parse_page(args.auction))
    lots.sort(key=base.sort_key)
    comps, dropped = parse_ebay(args.ebay)
    print(f'{len(lots)} lots | {len(comps)} usable eBay comps')
    for k, v in dropped.most_common():
        print(f'  dropped {k}: {v}')

    rows = match(lots, comps)
    build(rows, comps, args.out)
    write_profit_csv(rows, args.out)
    cov = sum(1 for r in rows if r['ebay_n'])
    print(f'eBay-matched lots: {cov}/{len(rows)} | cashout-matched: '
          f'{sum(1 for r in rows if r["sc_lo"])}/{len(rows)}')
    print(f'wrote {args.out}.xlsx')
    print('NOTE: run scripts/recalc.py to cache formula values before sharing.')


if __name__ == '__main__':
    main()
