"""Compare native coordinates against Tychosium's rounded text export."""
import argparse
import csv
import math
import re
from datetime import datetime

def parse_angle(value, ra=False):
    numbers = re.findall(r'\d+(?:\.\d+)?', value)
    if len(numbers) != 3:
        return None
    x = float(numbers[0]) + float(numbers[1])/60 + float(numbers[2])/3600
    return x*15 if ra else (-x if value.startswith('-') else x)

def read_reference(path):
    out, body = {}, None
    with open(path, encoding='utf-8-sig') as file:
        for line in file:
            if line.startswith('PLANET:'):
                body = line.split(':', 1)[1].strip().title()
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 5 or not re.match(r'^\d{4}-\d{2}-\d{2}$', parts[0]):
                continue
            ra, dec = parse_angle(parts[2], True), parse_angle(parts[3])
            distance = re.match(r'([\d.]+)\s*(km|AU)', parts[4], re.I)
            if ra is None or dec is None or not distance:
                continue
            km = float(distance[1]) * (149597870.7 if distance[2].lower() == 'au' else 1)
            out[(body, datetime.fromisoformat(parts[0]+'T'+parts[1]))] = (ra, dec, km, distance[2].lower())
    return out

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('python_csv'); parser.add_argument('tychosium_txt')
    args = parser.parse_args()
    ref = read_reference(args.tychosium_txt)
    stats = {}
    with open(args.python_csv, newline='', encoding='utf-8-sig') as file:
        for row in csv.DictReader(file):
            key = (row['body'], datetime.fromisoformat(row['datetime_utc']).replace(tzinfo=None))
            if key not in ref:
                continue
            ra, dec, distance, unit = ref[key]
            dr = (float(row['ra_deg_native'])-ra+180)%360-180
            dd = float(row['dec_deg_native'])-dec
            a, b, c, d = map(math.radians, [float(row['ra_deg_native']), float(row['dec_deg_native']), ra, dec])
            separation = math.degrees(math.acos(max(-1,min(1,math.sin(b)*math.sin(d)+math.cos(b)*math.cos(d)*math.cos(a-c)))))
            stats.setdefault(key[0], []).append((dr, dd, separation, float(row['distance_km'])-distance, unit))
    if not stats:
        raise SystemExit('No matching body/date rows. Check the interval and files.')
    for body, values in stats.items():
        print(f'{body}: {len(values)} matching rows')
        for i, name in enumerate(['RA difference (deg)', 'DEC difference (deg)', 'angular separation (deg)', 'distance difference (km)']):
            nums = [v[i] for v in values]
            print(f'  {name}: mean={sum(nums)/len(nums):.8f}, RMS={math.sqrt(sum(x*x for x in nums)/len(nums)):.8f}, max_abs={max(map(abs,nums)):.8f}')
        if any(v[4] == 'au' for v in values):
            print('  Note: Tychosium AU distance is rounded to 0.01 AU; distance comparison is coarse.')
    for body in ('Moon','Sun','Mars'):
        if body not in stats:
            print(f'{body}: no matched rows')

if __name__ == '__main__':
    main()
