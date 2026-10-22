# Python TYCHOS

A headless experimental model of Earth, Moon, Sun and Mars. It targets Tychosium's `uncoupled-moon` configuration, with actual planet sizes, lunar node, plane and apsidal geometry, and no equant or solar coupling. It exports native geometric coordinates; it is not yet a validated astronomical ephemeris or an optimization system.

## Three commands

Run these from the project folder in PowerShell. Python 3.8 or newer is required; no third-party packages are needed.

### 1. Generate Python TYCHOS ephemerides

```powershell
py -3 tychos.py --start 2000-06-21 --end 2001-06-21 --step-hours 3 --output data/ephemeris_python.csv
```

Adjust the dates and step as needed. Dates are UTC; the end date is included if it falls on a sample. If the CSV already exists, choose another output name or add `--overwrite` to replace it.

### 2. Compare with JPL

Place the TSN Horizons bundle in `data/jpl_ephemerides.txt`, with matching bodies, dates, cadence and a geocentric observer. Then run:

```powershell
py -3 scripts/compare_jpl.py data/ephemeris_python.csv data/jpl_ephemerides.txt --jpl-frame apparent-of-date --output reports/jpl_comparison.txt
```

The report is saved in `reports`; it will not overwrite an existing file. Choose another name or move the old report. You can select `icrf` instead of `apparent-of-date` if that reference column is present.

**Frame warning:** Python outputs native geometric coordinates. JPL observer coordinates have different frame and apparent/astrometric conventions; the script does not transform frames or apply light-time corrections. This is a diagnostic comparison, not a rigorously frame-matched accuracy assessment. JPL distance conventions can differ from geometric distance too.

### 3. Compare with Tychosium

Export Moon, Sun and Mars from Tychosium with the same dates and cadence, using `uncoupled-moon` and actual planet sizes. Save the text file as `data/tychos_ephemerides.txt`, then run:

```powershell
py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt | Tee-Object -FilePath reports/tychosium_comparison.txt
```

This displays and saves the report. `Tee-Object` replaces an existing report of the same name.

## Validation status

For 2000-06-21–2001-06-21 at three-hour intervals, Moon, Sun and Mars agree with the Tychosium text export within its angular rounding precision; lunar distance differs by 0.29 km RMS. Sun and Mars distances are rounded to 0.01 AU in that export, so precise distance equivalence remains unverified. Longer intervals, higher-precision distances and consistent reference frames still need investigation. Keep settings and export configuration with each baseline.

## Lunar geometry evaluator

`lunar_baseline.json` contains the current node, plane, apsidal and lunar-orbit parameters. Copy it to a new JSON file before experimenting; angles are in degrees, speeds in radians per 365.2425-day model year, and radii in model units (0.01 AU). All four sections and their existing fields are required; no additional deferent or automatic optimization is implemented yet.

Evaluate a configuration with `py -3 scripts/evaluate_moon.py --config lunar_baseline.json --jpl data/jpl_ephemerides.txt --output reports/moon_baseline.json`. The output will not overwrite an existing file. It records the complete parameters, JPL file hash, sample counts and RA, DEC, angular and distance mean/RMS/max, separately for historical 1800–1999, training 2000–2010 and validation 2011–2026 (UTC calendar years). Empty or partial intervals reflect the supplied data; check their counts and dates. The split is for evaluation only and no fitting is performed. Native geometric vs JPL apparent-of-date and the difference in distance conventions have the same limitations described above.
