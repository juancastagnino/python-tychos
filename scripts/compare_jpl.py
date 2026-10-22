"""Diagnostic comparison against a TSN JPL Horizons observer bundle."""
import argparse
import csv
import math
import re
from datetime import datetime
from pathlib import Path

AU_KM = 149597870.7
MONTHS = {name: i for i, name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'), 1)}

def angle(value, ra=False):
    parts = value.strip().split()
    if len(parts) != 3:
        raise ValueError(f'Invalid Horizons sexagesimal angle: {value!r}')
    number = abs(float(parts[0])) + float(parts[1])/60 + float(parts[2])/3600
    return number * 15 if ra else (-number if parts[0].startswith('-') else number)

def read_horizons(path, mode):
    rows, body, header, in_data = {}, None, None, False
    with open(path, encoding='utf-8-sig', newline='') as handle:
        for line in handle:
            if line.startswith('# REQUEST BODY:'):
                body = line.split(':', 1)[1].strip().title()
                header = None
            elif 'Date__(UT)' in line and 'R.A.' in line:
                header = [part.strip() for part in next(csv.reader([line]))]
            elif line.strip() == '$$SOE':
                if not body or not header:
                    raise ValueError('Expected REQUEST BODY and CSV header before $$SOE')
                in_data = True
            elif line.strip() == '$$EOE':
                in_data = False
            elif in_data:
                fields = next(csv.reader([line]))
                stamp = fields[0].strip()
                match = re.fullmatch(r'(\d{4})-([A-Za-z]{3})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?', stamp)
                if not match:
                    raise ValueError(f'Unsupported date: {stamp!r}')
                year, month, day, hour, minute, second = match.groups()
                date = datetime(int(year), MONTHS[month.title()], int(day), int(hour), int(minute), int(second))
                suffix = '(ICRF)' if mode == 'icrf' else '(a-app)'
                ra_index = next(i for i, h in enumerate(header) if h.startswith('R.A.') and suffix in h)
                dec_index = next(i for i, h in enumerate(header) if h.startswith('DEC') and suffix in h)
                distance_index = header.index('delta')
                key = (body, date)
                if key in rows:
                    raise ValueError(f'Duplicate Horizons sample: {key}')
                rows[key] = (angle(fields[ra_index], True), angle(fields[dec_index]), float(fields[distance_index])*AU_KM)
    if not rows:
        raise ValueError('No Horizons samples found')
    return rows

def compare(python_path, reference):
    stats, missing = {}, {}
    with open(python_path, newline='', encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            date = datetime.fromisoformat(row['datetime_utc']).replace(tzinfo=None)
            key = (row['body'], date)
            if key not in reference:
                missing[key[0]] = missing.get(key[0], 0) + 1
                continue
            ra, dec, km = reference[key]
            pra, pdec = float(row['ra_deg_native']), float(row['dec_deg_native'])
            dra = (pra-ra+180)%360-180
            a,b,c,d = map(math.radians, (pra,pdec,ra,dec))
            sep = math.degrees(math.acos(max(-1.0,min(1.0,math.sin(b)*math.sin(d)+math.cos(b)*math.cos(d)*math.cos(a-c)))))
            stats.setdefault(key[0], []).append((dra, pdec-dec, sep, float(row['distance_km'])-km))
    if not stats:
        raise ValueError('No matching body/date rows')
    return stats, missing

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('python_csv'); p.add_argument('jpl_txt')
    p.add_argument('--jpl-frame', choices=['apparent-of-date','icrf'], required=True)
    p.add_argument('--output', help='Optional report file; existing files are not overwritten')
    args = p.parse_args()
    try:
        reference = read_horizons(args.jpl_txt, args.jpl_frame)
        stats, missing = compare(args.python_csv, reference)
        lines = ['Python TYCHOS vs JPL Horizons — diagnostic comparison',
                 f'Python: native geometric, geocentric; JPL: {args.jpl_frame} observer coordinates',
                 'CAUTION: frames and apparent/geometric conventions are not verified equivalent.',
                 'RA/DEC are signed Python minus JPL in degrees; separation is non-negative.',
                 'Distance is Python geometric minus JPL observer delta (light-time conventions may differ), km.', '']
        for body, values in sorted(stats.items()):
            lines.append(f'{body}: {len(values)} matched; {missing.get(body, 0)} Python rows unmatched')
            for index, label in enumerate(('RA (deg)', 'Declination (deg)', 'Angular separation (deg)', 'Distance (km)')):
                samples = [row[index] for row in values]
                lines.append(f'  {label}: mean={sum(samples)/len(samples):.8f}, RMS={math.sqrt(sum(x*x for x in samples)/len(samples)):.8f}, max_abs={max(map(abs,samples)):.8f}')
        for body, count in sorted(missing.items()):
            if body not in stats: lines.append(f'{body}: 0 matched; {count} Python rows unmatched')
        report = '\n'.join(lines) + '\n'
        if args.output:
            with Path(args.output).open('x', encoding='utf-8', newline='') as handle: handle.write(report)
        print(report, end='')
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        p.exit(1, f'Comparison failed: {exc}\n')

if __name__ == '__main__':
    main()
