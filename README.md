# Python TYCHOS: exploratory prototype

This project will implement a headless geometric model and CSV ephemeris export. The intended hierarchy is Earth on the PVP; Moon and Sun under Earth; Mars under Sun. The Moon is to use a uniformly traversed local circle, with nodal, plane and apsidal stages, initially without an equant or solar coupling.

This is a research model, not yet validated against Tychosium or observations. Frame conventions and exact transform order must be verified before claiming equivalence.

## Initial prototype

Run `py -3 tychos.py --start 2000-06-21 --end 2000-06-22 --step-hours 3`. The default output is `data/ephemeris_python.csv`. Existing files are protected: use `--overwrite` to replace one, or `--output` to choose another path.

The CSV contains Earth-relative world-frame vectors, native equatorial RA/DEC and distances for Moon, Sun and Mars. Its geometry targets Tychosium's `uncoupled-moon` branch with actual planet sizes. Solar coupling and equant are absent. These are geometric, native-frame coordinates, not JPL apparent positions. The implementation and constants still require validation across dates and bodies; no optimization is implemented.

Compare with a Tychosium text export using `py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt`. Run tests with `py -3 -m unittest discover -s scripts -p "test_*.py"`. Tychosium's text output rounds RA to one second of time, DEC to one arcsecond, Moon distance to km and AU distances to 0.01 AU; results cannot establish equivalence beyond that precision. Capture settings and software revision alongside exports.

Validation against the `uncoupled-moon` Tychosium text export for 2000-06-21–2001-06-21 at three-hour intervals: Moon, Sun and Mars agree in angular coordinates within the export's rounding precision (RA is rounded to one second of time); Moon distance RMS difference is 0.29 km, within its 1 km display rounding. Sun and Mars distances are displayed to 0.01 AU, insufficient for precise distance validation. This is one interval and one configuration, not proof of full equivalence. Longer intervals and high-precision exports remain to be checked before fitting.

## Requirements and useful commands

Python 3.8 or newer is required. No third-party packages are needed. Run these commands in PowerShell from the project folder; on other systems replace `py -3` with `python3`.

Generate one year of samples every three hours:

```powershell
py -3 tychos.py --start 2000-06-21 --end 2001-06-21 --step-hours 3 --output data/ephemeris_python.csv
```

The default is also `data/ephemeris_python.csv`; to replace an existing file add `--overwrite`. To save a different interval separately:

```powershell
py -3 tychos.py --start 1800-06-21 --end 2026-06-21 --step-hours 24 --output data/long_interval.csv
py -3 tychos.py --help
```

Dates are UTC, and the end is included when it falls on a sample. One model unit is 0.01 AU.

To compare, export Moon, Sun and Mars from Tychosium using `uncoupled-moon`, actual planet sizes, and the same dates and cadence. Save the file as `data/tychos_ephemerides.txt` and run:

```powershell
py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt
py -3 -m unittest discover -s scripts -p "test_*.py" -v
```

To also save the comparison in `reports`, use PowerShell's `Tee-Object` (this replaces an existing file with that name):

```powershell
py -3 scripts/compare_tychosium.py data/ephemeris_python.csv data/tychos_ephemerides.txt | Tee-Object -FilePath reports/tychosium_comparison.txt
```

The comparator does not currently have an `--output` option; `Tee-Object` displays and saves its output. JPL comparison is not yet implemented.

Keep the settings, branch and date range with any baseline. A future comparison against JPL or observations must use compatible reference frames and record the reference product and uncertainties. JPL ephemerides are model-derived products informed by observations, not raw observations. The model search and reinforcement learning described as future research are not yet implemented.
