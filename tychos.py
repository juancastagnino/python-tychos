"""Exploratory geometric ephemeris; not a validated Tychosium reproduction."""
import argparse
import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

AU_KM = 149_597_870.7
EPOCH = datetime(2000, 6, 21, 12, tzinfo=timezone.utc)
YEAR_DAYS = 365.2425
LUNAR_DEFAULTS = {
    'node': {'speed': -0.33780566, 'start_deg': -296.0},
    'plane': {'tilt_x_deg': 0.1, 'tilt_z_deg': -5.2},
    'apsidal': {'speed': 0.71015440177343, 'start_deg': 167.51, 'radius': 0.028147459454447972},
    'orbit': {'speed': 83.28521004, 'start_deg': 318.0, 'radius': 0.25695552897999907},
}

def add(a, b):
    return tuple(x + y for x, y in zip(a, b))

def ry(v, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    return (c*x + s*z, y, -s*x + c*z)

def rz(v, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    return (c*x-s*y, s*x+c*y, z)

def rx(v, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    return (x, c*y-s*z, s*y+c*z)

def phase(speed, start_deg, t):
    return speed*t - math.radians(start_deg)

def positions(date, lunar_config=None):
    """World axes follow Three.js-style Y rotations; length unit = 0.01 AU."""
    t = (date - EPOCH).total_seconds() / 86400 / YEAR_DAYS
    earth_angle = phase(-0.0002479160869310127, 0, t)
    earth = ry((37.8453, 0, 0), earth_angle)
    # Nodal conjugation and inherited apsidal orientation match the plot hierarchy.
    lunar_config = LUNAR_DEFAULTS if lunar_config is None else lunar_config
    node_config, plane, apsidal, orbit = (lunar_config[k] for k in ('node', 'plane', 'apsidal', 'orbit'))
    node = phase(node_config['speed'], node_config['start_deg'], t)
    apsis = phase(apsidal['speed'], apsidal['start_deg'], t)
    moon_phase = phase(orbit['speed'], orbit['start_deg'], t)
    local_moon = ry((orbit['radius'], 0, 0), moon_phase)
    # Candidate double-circle decomposition in the apsidal frame. Both
    # vectors use linear phases; angles and signs are experimental choices.
    circles = lunar_config.get('double_epicycle', {})
    first_angle = circles.get('first_rate_factor', -1)*moon_phase + math.radians(circles.get('first_phase_deg', 180))
    second_angle = circles.get('second_rate_factor', 2)*moon_phase + math.radians(circles.get('second_phase_deg', 0))
    local_moon = add(local_moon, ry((circles.get('first_radius', 0), 0, 0), first_angle))
    local_moon = add(local_moon, ry((circles.get('second_radius', 0), 0, 0), second_angle))
    lunar = ry(add((apsidal['radius'], 0, 0), local_moon), apsis)
    lunar = ry(lunar, -node)
    lunar = ry(rx(rz(lunar, math.radians(plane['tilt_z_deg'])), math.radians(plane['tilt_x_deg'])), node)
    solar = add((3.3, 0, -0.645), rx(ry((100, 0, 0), 2*math.pi*t), math.radians(0.2762)))
    sun = add(earth, ry(solar, earth_angle))
    lunar_world = ry(lunar, earth_angle)
    # Experimental libration: rotate the complete Earth-Moon vector around
    # the model's world Y axis, using the unmodified projected elongation.
    libration = lunar_config.get('solar_libration', {}).get('amplitude_deg', 0)
    if libration:
        sun_vector = ry(solar, earth_angle)
        moon_lon0 = math.atan2(-lunar_world[2], lunar_world[0])
        sun_lon0 = math.atan2(-sun_vector[2], sun_vector[0])
        lunar_world = ry(lunar_world, math.radians(libration)*math.sin(2*(moon_lon0-sun_lon0)))
    uncorrected_lunar_world = lunar_world
    # Match Tychosium's world-XZ angle convention and its reflected radial
    # projection. Angles use the uncorrected Moon, without feedback.
    coupling = lunar_config.get('solar_coupling', {})
    moon_lon = math.atan2(-lunar_world[2], lunar_world[0])
    sun_vector = ry(solar, earth_angle)
    sun_lon = math.atan2(-sun_vector[2], sun_vector[0])
    elongation = moon_lon - sun_lon
    length_sq = sum(v*v for v in lunar_world)
    for amplitude, argument in ((coupling.get('eccentric_radius', 0), 2*elongation-moon_phase),
                                (coupling.get('variation_radius', 0), 2*elongation)):
        direction = moon_lon + argument
        displacement = (amplitude*math.cos(direction), 0, -amplitude*math.sin(direction))
        dot = sum(a*b for a, b in zip(displacement, uncorrected_lunar_world)) / length_sq
        lunar_world = add(lunar_world, tuple(d - 2*dot*v for d, v in zip(displacement, uncorrected_lunar_world)))
    # Experimental two equal circular vectors: their resultant is radial in
    # the ecliptic projection, with a cosine variation in apsidal phase.
    # It is not a reconstruction of Longomontanus's historical construction.
    radial = lunar_config.get('paired_radial', {}).get('radius', 0)
    if radial:
        apsis_axis = ry((1, 0, 0), apsis)
        apsis_axis = ry(apsis_axis, -node)
        apsis_axis = ry(rx(rz(apsis_axis, math.radians(plane['tilt_z_deg'])), math.radians(plane['tilt_x_deg'])), node)
        apsis_axis = ry(apsis_axis, earth_angle)
        apsis_lon = math.atan2(-apsis_axis[2], apsis_axis[0])
        for direction in (apsis_lon, 2*moon_lon-apsis_lon):
            lunar_world = add(lunar_world, (radial*math.cos(direction), 0, -radial*math.sin(direction)))
    moon = add(earth, lunar_world)
    # Sun-relative Mars adapter: position inherits Sun, axes inherit the
    # Earth/Sun-Mars binary frame, not the Sun's own annual rotation.
    long_phase = phase(0.3974599, -114.8723, t)
    mars_phase = phase(-3.33985, 119.358, t)
    long_position = rz(ry((7.12013, 0, 0), long_phase), math.radians(-0.3))
    main = rz(ry((152.677, 0, 0), mars_phase), math.radians(-2.109))
    main = rz(ry(main, long_phase), math.radians(-0.3))
    mars_local = add((7.62, 0.232, -20), ry(add(long_position, main), 2*math.pi*t))
    mars = add(sun, ry(mars_local, earth_angle))
    return earth, moon, sun, mars

def equatorial(vector, date):
    t = (date - EPOCH).total_seconds() / 86400 / YEAR_DAYS
    # Inverse of Earth orbit orientation, then inverse cSphere Rx(tiltb) Rz(tilt).
    vector = ry(vector, -phase(-0.0002479160869310127, 0, t))
    vector = rx(vector, math.radians(-0.26))
    return rz(vector, math.radians(23.439062))

def parse_date(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=timezone.utc) if '+' not in value and not value.endswith('Z') else datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)

def export(start, end, hours, output, overwrite=False, lunar_config=None):
    if hours <= 0 or end < start:
        raise ValueError('step must be positive and end must not precede start')
    with open(output, 'w' if overwrite else 'x', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['datetime_utc', 'body', 'earth_relative_x_model', 'earth_relative_y_model', 'earth_relative_z_model', 'ra_deg_native', 'dec_deg_native', 'distance_km'])
        current = start
        while current <= end:
            earth, moon, sun, mars = positions(current, lunar_config)
            for name, target in [('Moon', moon), ('Sun', sun), ('Mars', mars)]:
                v = tuple(a-b for a,b in zip(target, earth))
                eq = equatorial(v, current)
                distance = math.sqrt(sum(x*x for x in v))
                ra = math.degrees(math.atan2(eq[0], eq[2])) % 360
                dec = math.degrees(math.asin(eq[1]/distance))
                writer.writerow([current.isoformat(), name, *v, ra, dec, distance*AU_KM/100])
            current += timedelta(hours=hours)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='UTC ISO date or datetime')
    parser.add_argument('--end', required=True, help='UTC ISO date or datetime')
    parser.add_argument('--step-hours', type=float, required=True)
    parser.add_argument('--output', default=str(Path(__file__).resolve().parent / 'data' / 'ephemeris_python.csv'), help='CSV output path (default: data/ephemeris_python.csv)')
    parser.add_argument('--overwrite', action='store_true', help='replace an existing output file')
    parser.add_argument('--lunar-config', help='optional JSON lunar configuration')
    args = parser.parse_args()
    config = None
    if args.lunar_config:
        import json
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
        from evaluate_moon import validate
        config = validate(json.loads(Path(args.lunar_config).read_text(encoding='utf-8')))
    export(parse_date(args.start), parse_date(args.end), args.step_hours, args.output, args.overwrite, config)

if __name__ == '__main__':
    main()
