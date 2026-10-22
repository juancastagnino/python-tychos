"""Evaluate one explicit lunar geometry against Horizons, without optimizing."""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tychos
from compare_jpl import read_horizons

SPLITS = {'historical': (1800, 2000), 'train': (2000, 2011), 'validation': (2011, 2027)}

def validate(config):
    optional = {'solar_coupling': {'eccentric_radius': 0, 'variation_radius': 0}, 'paired_radial': {'radius': 0},
                'double_epicycle': {'first_radius': 0, 'second_radius': 0, 'first_phase_deg': 180, 'second_phase_deg': 0},
                'solar_libration': {'amplitude_deg': 0}}
    if not isinstance(config, dict) or not set(tychos.LUNAR_DEFAULTS) <= set(config) or set(config) - set(tychos.LUNAR_DEFAULTS) - set(optional):
        raise ValueError('Configuration requires node, plane, apsidal and orbit; experimental sections are optional')
    for name, defaults in {**tychos.LUNAR_DEFAULTS, **optional}.items():
        if name not in config:
            continue
        allowed_extra = {'first_rate_factor', 'second_rate_factor'} if name == 'double_epicycle' else set()
        if not isinstance(config[name], dict) or not set(defaults) <= set(config[name]) or set(config[name]) - set(defaults) - allowed_extra:
            raise ValueError(f'{name} must contain exactly: {sorted(defaults)}')
        for key, value in config[name].items():
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError(f'{name}.{key} must be a finite number')
    if config['orbit']['radius'] <= 0:
        raise ValueError('orbit.radius must be positive')
    return config

def summarize(samples):
    labels = ('ra_deg', 'dec_deg', 'angular_separation_deg', 'distance_km')
    return {name: {'mean': sum(row[i] for row in samples)/len(samples),
                   'rms': math.sqrt(sum(row[i]**2 for row in samples)/len(samples)),
                   'max_abs': max(abs(row[i]) for row in samples)} for i, name in enumerate(labels)}

def evaluate(config, reference):
    groups = {name: [] for name in SPLITS}
    dates = {name: [] for name in SPLITS}
    for (body, stamp), (ra, dec, distance_km) in sorted(reference.items(), key=lambda item: item[0][1]):
        if body != 'Moon': continue
        group = next((name for name, (start, end) in SPLITS.items() if start <= stamp.year < end), None)
        if group is None: continue
        date = stamp.replace(tzinfo=timezone.utc)
        earth, moon, _, _ = tychos.positions(date, config)
        vector = tuple(a-b for a,b in zip(moon, earth))
        x,y,z = tychos.equatorial(vector, date)
        length = math.sqrt(sum(v*v for v in vector))
        pra = math.degrees(math.atan2(x,z)) % 360
        pdec = math.degrees(math.asin(max(-1,min(1,y/length))))
        dra = (pra-ra+180)%360-180
        a,b,c,d = map(math.radians, (pra,pdec,ra,dec))
        sep = math.degrees(math.acos(max(-1,min(1,math.sin(b)*math.sin(d)+math.cos(b)*math.cos(d)*math.cos(a-c)))))
        groups[group].append((dra, pdec-dec, sep, length*tychos.AU_KM/100-distance_km))
        dates[group].append(stamp)
    result = {}
    for name, rows in groups.items():
        result[name] = {'sample_count': len(rows), 'first_utc': dates[name][0].isoformat() if rows else None,
                        'last_utc': dates[name][-1].isoformat() if rows else None,
                        'metrics': summarize(rows) if rows else None}
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='lunar_baseline.json')
    p.add_argument('--jpl', default='data/jpl_ephemerides.txt')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    try:
        config = validate(json.loads(Path(args.config).read_text(encoding='utf-8')))
        source = Path(args.jpl)
        reference = read_horizons(source, 'apparent-of-date')
        splits = evaluate(config, reference)
        if not any(s['sample_count'] for s in splits.values()): raise ValueError('No Moon samples in defined intervals')
        result = {'model': 'geometric Moon; optional experimental geometries; no equant', 'configuration': config,
                  'reference': {'file': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                'frame': 'JPL apparent-of-date vs native geometric',
                                'warning': 'Frames and light-time conventions differ; diagnostic comparison only.'},
                  'split_definition': 'UTC years: historical [1800,2000), train [2000,2011), validation [2011,2027)',
                  'splits': splits}
        with Path(args.output).open('x', encoding='utf-8') as handle: json.dump(result, handle, indent=2, allow_nan=False); handle.write('\n')
        for name, data in splits.items():
            print(f"{name}: {data['sample_count']} samples" + (f", angular RMS {data['metrics']['angular_separation_deg']['rms']:.6f} deg, distance RMS {data['metrics']['distance_km']['rms']:.1f} km" if data['metrics'] else ' (no data)'))
        print(f'Saved {args.output}')
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        p.exit(1, f'Evaluation failed: {exc}\n')

if __name__ == '__main__': main()
