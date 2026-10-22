# Lunar geometry: research scenarios

This is an experimental kinematic investigation, not a physical explanation or a validated historical reconstruction. JPL Horizons predictions are observationally constrained model products; native geometric and apparent-of-date comparisons have frame and light-time differences.

## Starting point

`lunar_half_apsidal_uncoupled.json` isolates the half-radius apsidal geometry with no solar coupling, paired radial offsets, double epicycle or equant. It is a control for later Sun-related libration tests; its starting angles are inherited from the current uncoupled baseline and have not been optimized for this radius.

`lunar_half_apsidal_solar.json` changes only that control's solar coupling to the hierarchy-refinement values. The libration, paired radial geometry, double epicycle and equant remain absent. Python solar-coupling parity with Tychosium is still unverified.

## Solar libration experiment

`lunar_solar_libration_experiment.json` uses the same half-radius control, with an optional angular oscillation applied to the whole Earth–Moon vector around world Y. The angle is amplitude times sin(2D), where D is the unmodified Moon–Sun projected world-XZ elongation. This is an explicit analytical angular modulation of the physical model position, not a uniform-circle construction, an export correction, or a faithful reconstruction of Brahe's epicycle-center libration. It preserves the Earth–Moon vector length exactly but does not preserve the existing inclined orbital plane. Its phase is tied to the unmodified Moon and Sun without feedback. Solar coupling, paired radial offsets and equant are absent in this configuration. The baseline has amplitude zero; the sweep tests both signs at 0.3375 and 0.675 degrees. The 0.675-degree scale is historically motivated, not proof of equivalence. If promising, a geometric implementation and orbital-plane treatment require separate investigation. Source: https://en.wikisource.org/wiki/Page:Tycho_brahe.djvu/369.

The uncoupled Python baseline reproduces Tychosium's uncoupled Moon to export precision. The double apsidal radius improves the angular result but has a large distance residual. Earlier Tychosium diagnostics reported a roughly 21,110 km apsidal-period distance residual and about 3,054 km residual RMS after removing that harmonic mathematically. This was a diagnostic, not an improved ephemeris; its interval, convention and implementation must be checked again before interpreting it as a physical displacement.

## Solar coupling

The optional `solar_coupling` ports the hierarchy-refinement implementation: uncorrected Earth–Moon and Earth–Sun world XZ directions define 2D-M and 2D directions; each offset has its radial projection reflected using the full uncorrected Earth–Moon vector. It is a positional geometry in the model, not an export correction. `lunar_solar_experiment.json` enables the saved values and keeps the equant absent. Exact parity against a matching actual-size Tychosium export remains to be verified; do not assume it from the source translation alone.

## Paired radial experiment

An optional pair of equal planar displacement vectors has orientations apsis and twice the uncorrected projected lunar longitude minus apsis. Their sum lies along the projected lunar direction and varies with apsidal phase. A radius of 0.007055 model units per vector is approximately 10,554 km; test both signs since the sign depends on conventions. This is approximate radial action in the XZ projection, not exact 3D radial motion. The derived projected angles need not rotate uniformly when inclination and the other motions are included. The resulting path is not necessarily a uniformly traversed circle.

This construction is inspired by the earlier diagnostic, not a historical reproduction of Brahe or Longomontanus. It introduces a fitted geometric degree of freedom; matching data would not itself establish a physical cause or PVP origin. It is disabled by default. Compare the zero-radius solar baseline and both signs before further fitting.

## Historical double epicycle and libration

The separate `lunar_double_epicycle_experiment.json` is a first equant-free candidate, not a verified reconstruction. It disables solar coupling and paired radial geometry and sets the apsidal displacement to zero, while preserving the rotating apsidal orientation. The two radii are 0.058 and 0.029 times the main lunar radius. In the apsidal frame the main vector angle is M, the first displacement angle is -M plus a phase, and the second is 2M plus a phase. Thus their rates in that frame are opposite with a 2:1 ratio; whether that reference frame and arrangement match the historical construction remains unverified. The phase choices are provisional and tested in combination. Moving the local vectors through the tilted precessing plane produces compound motion in world coordinates. No libration, evection, equant or solar coupling is included.

As a separate future experiment, derive the historical two-epicycle construction, its phases, speed ratios and frame conventions from original or scholarly technical sources before coding it. It may offer an alternative distance/direction trade-off but is not equivalent by assumption to the paired-radial construction above. Distinguish it from the solar-phase libration used for variation. Scholarly accounts also describe equant motion in the final lunar theory; the precise historical relationship needs examination. See https://authors.library.caltech.edu/records/anzsj-kgz73.

### Second candidate: apsis-aligned first displacement

`lunar_double_epicycle_02.json` tests a different interpretation: the main vector rotates at M, the first offset is fixed in the apsidal frame, and the second rotates at -M. The frame itself precesses. Starting the first and second offsets in opposite directions gives a combined offset of 0.029 times the main radius at M=0 and 0.087 at M=180 degrees, in the same absolute direction; the projected radial signs are opposite at those two points. This reproduces the stated extremal ratios only under the assumed phase and orientation, not the complete historical construction. Its absolute apsidal-frame rates are 0 and -1 times M, so it is not a verified implementation of the reported opposite-direction 2:1 rate. The four phase combinations test the ambiguity; no solar terms, equant or apsidal center displacement are used. Compare with the original uncoupled baseline and the earlier experimental report, not only the sweep's baseline. Source: https://en.wikisource.org/wiki/Page:Tycho_brahe.djvu/368.

## Acceptance checks

First establish solar-coupling parity with a same-date Tychosium export. Then compare angular RA, declination and separation, distance RMS, extrema and selected dates, as well as historical, training and validation periods. Analyze residuals by apsidal and solar phase; avoid accepting a candidate solely on a single metric. A close fit or numerical coincidence cannot establish a unique geometry or physical mechanism.
