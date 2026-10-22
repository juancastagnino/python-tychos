"""Evaluate baseline and one-parameter-at-a-time lunar candidates."""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
from compare_jpl import read_horizons
from evaluate_moon import evaluate, validate

def candidates(baseline, values):
    if not isinstance(values, dict) or not values:
        raise ValueError('Sweep values must be a non-empty object')
    result = [('baseline', None, None, copy.deepcopy(baseline))]
    for name, options in values.items():
        parts = name.split('.')
        if len(parts) != 2 or parts[0] not in baseline or parts[1] not in baseline[parts[0]]:
            raise ValueError(f'Unknown parameter: {name}')
        if not isinstance(options, list) or not options:
            raise ValueError(f'{name} must contain a non-empty array')
        seen = set()
        for value in options:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'{name}: values must be finite numbers')
            if value in seen or value == baseline[parts[0]][parts[1]]:
                continue
            seen.add(value)
            config = copy.deepcopy(baseline)
            config[parts[0]][parts[1]] = value
            validate(config)
            result.append((f'candidate_{len(result):03d}', name, value, config))
    return result

def main(candidate_factory=candidates, default_values='scripts/lunar_sweep_values.json'):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='lunar_baseline.json')
    parser.add_argument('--values', default=default_values)
    parser.add_argument('--jpl', default='data/jpl_ephemerides.txt')
    parser.add_argument('--output-dir', required=True, help='New directory for results; must not already exist')
    parser.add_argument('--dry-run', action='store_true', help='List candidates without creating outputs')
    args = parser.parse_args()
    try:
        baseline = validate(json.loads(Path(args.baseline).read_text(encoding='utf-8')))
        values = json.loads(Path(args.values).read_text(encoding='utf-8'))
        runs = candidate_factory(baseline, values)
        print(f'{len(runs)} evaluations including baseline', flush=True)
        for label, name, value, _ in runs: print(f'  {label}: {name} = {value}' if name else '  baseline', flush=True)
        if args.dry_run: return
        reference_path = Path(args.jpl)
        reference = read_horizons(reference_path, 'apparent-of-date')
        if not any(body == 'Moon' and 1800 <= date.year < 2027 for body, date in reference):
            raise ValueError('No Moon samples in evaluation intervals')
        folder = Path(args.output_dir)
        folder.mkdir(parents=False, exist_ok=False)
        metadata = {'reference': str(reference_path), 'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                    'convention': 'native geometric vs JPL apparent-of-date; frames and distance conventions differ',
                    'split_years': {'historical': [1800, 2000], 'train': [2000, 2011], 'validation': [2011, 2027]},
                    'baseline': baseline, 'values': values, 'candidates': []}
        rows = []
        for label, name, value, config in runs:
            print(f'Evaluating {label}...', flush=True)
            splits = evaluate(config, reference)
            metadata['candidates'].append({'id': label, 'parameter': name, 'value': value, 'configuration': config, 'splits': splits})
            for split, result in splits.items():
                row = {'candidate': label, 'parameter': name or '', 'value': '' if value is None else value, 'split': split,
                       'sample_count': result['sample_count'], 'first_utc': result['first_utc'], 'last_utc': result['last_utc']}
                for metric, measures in (result['metrics'] or {}).items():
                    for measure, number in measures.items(): row[f'{metric}_{measure}'] = number
                rows.append(row)
        columns = ['candidate','parameter','value','split','sample_count','first_utc','last_utc'] + [f'{metric}_{measure}' for metric in ('ra_deg','dec_deg','angular_separation_deg','distance_km') for measure in ('mean','rms','max_abs')]
        with (folder / 'summary.csv').open('x', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader(); writer.writerows(rows)
        with (folder / 'details.json').open('x', encoding='utf-8') as handle:
            json.dump(metadata, handle, indent=2, allow_nan=False); handle.write('\n')
        print(f'Saved results in {folder}')
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        parser.exit(1, f'Sweep failed: {exc}\n')

if __name__ == '__main__': main()
