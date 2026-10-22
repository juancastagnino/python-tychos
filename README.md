# Python TYCHOS

Experimental headless Earth–Moon–Sun–Mars geometry based on Tychosium's `uncoupled-moon` branch. The lunar model uses node, plane and apsidal geometry, without equant or solar coupling. It is not a validated ephemeris or an automatic optimizer.

Run the following commands from the project folder in Windows PowerShell. Python 3.8+ is required; no external packages are needed.

## 1. Generate Python ephemerides

```powershell
py -3 tychos.py --start 1800-06-21 --end 2026-06-21 --step-hours 24 --output data/ephemeris_python.csv
```

Dates are UTC. Add `--overwrite` only if you want to replace an existing CSV.

## 2. Compare with JPL

Place the matching geocentric Horizons bundle in `data/jpl_ephemerides.txt`:

```powershell
py -3 scripts/compare_jpl.py data/ephemeris_python.csv data/jpl_ephemerides.txt --jpl-frame apparent-of-date --output reports/jpl_comparison.txt
```

The report must not already exist. Python native geometric and JPL apparent-of-date coordinates are not formally identical reference products; distance and light-time conventions also differ. Results are diagnostic comparisons.

## 3. Compare with Tychosium

Place the matching native export from `uncoupled-moon`, with actual planet sizes enabled, in `data/tychos_ephemerides.txt`:

```powershell
py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt | Tee-Object -FilePath reports/tychosium_comparison.txt
```

This command replaces an existing report. Tychosium's text rounding limits comparison precision, especially for distances in AU.

## 4. View parameters and proposed values

Edit `scripts/lunar_sweep_values.json`; each entry identifies one parameter and the values to test. Preview the baseline and candidates without running them:

```powershell
py -3 scripts/sweep_moon.py --output-dir reports/moon_sweep_01 --dry-run
```

`lunar_baseline.json` holds the unchanged starting configuration. Angles are degrees, speeds radians per 365.2425-day model year and radii in units of 0.01 AU.

## 5. Run the iterative analysis

```powershell
py -3 scripts/sweep_moon.py --output-dir reports/moon_sweep_01
```

The output folder must not already exist. Each candidate changes only one parameter from the baseline. Results are saved as `summary.csv` and `details.json`, with training (2000–2010), validation (2011–2026) and historical (1800–1999) metrics. Check sample dates and counts: intervals depend on the input data. The full sweep can take several minutes.

## 6. Generate a readable sweep summary

```powershell
py -3 scripts/summarize_sweep.py reports/moon_sweep_01/summary.csv --output reports/moon_sweep_01/summary.md
```

The Markdown ranks validation angular RMS and shows distance RMS separately, including changes relative to baseline. It does not pick one universally best solution. The output file must not already exist.

## 7. Run a combined sweep

Edit `scripts/combined_lunar_sweep_values.json` to select values. Every combination is evaluated against the unchanged baseline; the default grid contains 81 candidates plus the baseline. Preview the count before starting, as the number of combinations multiplies quickly:

```powershell
py -3 scripts/combined_sweep_moon.py --output-dir reports/moon_combined_01 --dry-run
py -3 scripts/combined_sweep_moon.py --output-dir reports/moon_combined_01
py -3 scripts/summarize_sweep.py reports/moon_combined_01/summary.csv --output reports/moon_combined_01/summary.md
```

The output directory and Markdown report must not already exist. Candidate parameters and their complete configurations are also recorded in `details.json`. The same JPL data, intervals and limitations apply as for the individual sweep.

## Experimental solar coupling and paired radial geometry

The default model and `lunar_baseline.json` remain uncoupled. `lunar_solar_experiment.json` enables the hierarchy-refinement solar terms, with the experimental paired radial geometry initially disabled. Its Tychosium parity still requires verification. See `moon_research_scenarios.md` for assumptions and alternatives.

```powershell
py -3 tychos.py --start 2000-06-21 --end 2001-06-21 --step-hours 24 --lunar-config lunar_solar_experiment.json --output data/ephemeris_solar_experiment.csv
py -3 scripts/sweep_moon.py --baseline lunar_solar_experiment.json --values scripts/paired_radial_sweep_values.json --output-dir reports/moon_paired_01
py -3 scripts/summarize_sweep.py reports/moon_paired_01/summary.csv --output reports/moon_paired_01/summary.md
```

The paired sweep tests both signs and the solar-coupled baseline. It requires the JPL input and a new output directory.

## Experimental double epicycle without equant

This separate, historically inspired candidate retains the apsidal orientation but sets its center displacement to zero. It has no solar coupling or equant and is not a verified historical reconstruction; see `moon_research_scenarios.md` for its precise assumptions.

```powershell
py -3 scripts/combined_sweep_moon.py --baseline lunar_double_epicycle_experiment.json --values scripts/double_epicycle_sweep_values.json --output-dir reports/moon_double_epicycle_01
py -3 scripts/summarize_sweep.py reports/moon_double_epicycle_01/summary.csv --output reports/moon_double_epicycle_01/summary.md
```

The four phase combinations include one baseline. Compare with the saved uncoupled baseline as well: the report's baseline is this experiment, not the previous model.

A second provisional arrangement tests the reported apogee/perigee displacement ratios using a different reference-frame interpretation:

```powershell
py -3 scripts/combined_sweep_moon.py --baseline lunar_double_epicycle_02.json --values scripts/double_epicycle_02_values.json --output-dir reports/moon_double_epicycle_02
py -3 scripts/summarize_sweep.py reports/moon_double_epicycle_02/summary.csv --output reports/moon_double_epicycle_02/summary.md
```

## Experimental solar libration

This is an analytical sin(2D) rotation of the Earth–Moon vector, not a uniform-circle construction or a faithful historical reconstruction. It preserves distance but can move the Moon out of its existing inclined plane. It is disabled in the original baseline. See `moon_research_scenarios.md` for the experiment's limitations.

```powershell
py -3 scripts/sweep_moon.py --baseline lunar_solar_libration_experiment.json --values scripts/solar_libration_sweep_values.json --output-dir reports/moon_solar_libration_01
py -3 scripts/summarize_sweep.py reports/moon_solar_libration_01/summary.csv --output reports/moon_solar_libration_01/summary.md
```

## Validation status

For 1800–2026 at daily cadence, Python and Tychosium angular results agree within text-export rounding; lunar distance differs by about 0.29 km RMS. Sun and Mars distance equivalence needs a higher-precision export. Keep settings and source data with each baseline. JPL ephemerides are model-derived products informed by observations, not raw independent observations.


resume of main commands:


python-tychos ephemerides generation:
py -3 tychos.py --start 1800-06-21 --end 2026-06-21 --step-hours 24 --output data/ephemeris_python.csv

comapre python-tychos with JPL
py -3 scripts/compare_jpl.py data/ephemeris_python.csv data/jpl_ephemerides.txt --jpl-frame apparent-of-date --output reports/jpl_comparison.txt

compare python-tychos with tychosium
py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt | Tee-Object -FilePath reports/tychosium_comparison.txt

Moon sweep univalue analysis
py -3 scripts/sweep_moon.py --output-dir reports/moon_sweep_01 

Sweep summary generation
py -3 scripts/summarize_sweep.py reports/moon_sweep_01/summary.csv --output reports/moon_sweep_01/summary.md

Combined sweep
py -3 scripts/combined_sweep_moon.py --output-dir reports/moon_combined_01

Combined summary
py -3 scripts/summarize_sweep.py reports/moon_combined_01/summary.csv --output reports/moon_combined_01/summary.md
