"""Exploratory geometric ephemeris; not a validated Tychosium reproduction."""
import argparse
import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

AU_KM = 149_597_870.7
EPOCH = datetime(2000, 6, 21, 12, tzinfo=timezone.utc)
YEAR_DAYS = 365.2425

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

def positions(date):
    """World axes follow Three.js-style Y rotations; length unit = 0.01 AU."""
    t = (date - EPOCH).total_seconds() / 86400 / YEAR_DAYS
    earth_angle = phase(-0.0002479160869310127, 0, t)
    earth = ry((37.8453, 0, 0), earth_angle)
    # Nodal conjugation and inherited apsidal orientation match the plot hierarchy.
    node = phase(-0.33780566, -296, t)
    apsis = phase(0.71015440177343, 167.51, t)
    moon_phase = phase(83.28521004, 318, t)
    local_moon = ry((0.25695552897999907, 0, 0), moon_phase)
    lunar = ry(add((0.028147459454447972, 0, 0), local_moon), apsis)
    lunar = ry(lunar, -node)
    lunar = ry(rx(rz(lunar, math.radians(-5.2)), math.radians(0.1)), node)
    moon = add(earth, ry(lunar, earth_angle))
    solar = add((3.3, 0, -0.645), rx(ry((100, 0, 0), 2*math.pi*t), math.radians(0.2762)))
    sun = add(earth, ry(solar, earth_angle))
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

def export(start, end, hours, output, overwrite=False):
    if hours <= 0 or end < start:
        raise ValueError('step must be positive and end must not precede start')
    with open(output, 'w' if overwrite else 'x', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['datetime_utc', 'body', 'earth_relative_x_model', 'earth_relative_y_model', 'earth_relative_z_model', 'ra_deg_native', 'dec_deg_native', 'distance_km'])
        current = start
        while current <= end:
            earth, moon, sun, mars = positions(current)
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
    args = parser.parse_args()
    export(parse_date(args.start), parse_date(args.end), args.step_hours, args.output, args.overwrite)

if __name__ == '__main__':
    main()
