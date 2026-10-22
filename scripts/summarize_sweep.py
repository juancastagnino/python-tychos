"""Summarize a lunar sweep without conflating angular and distance objectives."""
import argparse
import csv
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('summary_csv')
    parser.add_argument('--output', required=True, help='New Markdown report; existing files are not overwritten')
    args = parser.parse_args()
    try:
        with open(args.summary_csv, encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        selected = [r for r in rows if r['split'] == 'validation' and int(r['sample_count']) > 0]
        baseline = next(r for r in selected if r['candidate'] == 'baseline')
        angular = 'angular_separation_deg_rms'; distance = 'distance_km_rms'
        baseline_a, baseline_d = float(baseline[angular]), float(baseline[distance])
        if baseline_a <= 0 or baseline_d <= 0: raise ValueError('Baseline RMS must be positive')
        if any(r['sample_count'] != baseline['sample_count'] or r['first_utc'] != baseline['first_utc'] or r['last_utc'] != baseline['last_utc'] for r in selected):
            raise ValueError('Validation samples or date ranges do not match baseline')
        selected.sort(key=lambda r: float(r[angular]))
        lines = ['# Lunar sweep summary', '', 'Ranking uses validation angular-separation RMS only; distance is shown independently. No combined score or physical interpretation is assumed.',
                 '', f"Validation: {baseline['first_utc']} to {baseline['last_utc']}, {baseline['sample_count']} samples.",
                 '', 'Changes are relative to baseline: negative means lower error; positive means worse.', '',
                 '| Candidate | Parameter | Value | Angular RMS (°) | Change | Distance RMS (km) | Change |', '|---|---|---:|---:|---:|---:|---:|']
        for row in selected:
            a,d = float(row[angular]), float(row[distance])
            lines.append(f"| {row['candidate']} | {row['parameter'] or 'baseline'} | {row['value'] or '—'} | {a:.6f} | {(a/baseline_a-1)*100:+.2f}% | {d:,.1f} | {(d/baseline_d-1)*100:+.2f}% |")
        winners = [r['candidate'] for r in selected if r['candidate'] != 'baseline' and float(r[angular]) < baseline_a and float(r[distance]) < baseline_d]
        lines += ['', '**Improves both validation RMS metrics:** ' + (', '.join(winners) if winners else 'none'),
                  '', 'Compare train and historical rows in summary.csv before selecting a candidate. Native geometric vs JPL apparent-of-date is a diagnostic comparison; reference-frame and distance conventions differ.', '']
        report = '\n'.join(lines)
        with Path(args.output).open('x', encoding='utf-8') as handle: handle.write(report)
        print(f'Saved {args.output}')
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        parser.exit(1, f'Summary failed: {exc}\n')

if __name__ == '__main__': main()
