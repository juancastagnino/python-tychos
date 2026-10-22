import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tychos

class GeometryTests(unittest.TestCase):
    def test_rotations_preserve_length_and_invert(self):
        v = (2, -3, 5)
        for rotate in (tychos.rx, tychos.ry, tychos.rz):
            result = rotate(rotate(v, .4), -.4)
            for actual, expected in zip(result, v):
                self.assertAlmostEqual(actual, expected)

    def test_moon_reference_epoch_distance(self):
        earth, moon, sun, mars = tychos.positions(tychos.EPOCH)
        distance = math.dist(earth, moon) * tychos.AU_KM / 100
        self.assertAlmostEqual(distance, 416646, delta=1)
        self.assertGreater(math.dist(earth, sun), 90)
        self.assertGreater(math.dist(earth, mars), 1)

    def test_moon_export_direction_at_start(self):
        date = tychos.parse_date('2000-06-21')
        earth, moon, _, _ = tychos.positions(date)
        vector = tuple(a-b for a,b in zip(moon, earth))
        x, y, z = tychos.equatorial(vector, date)
        ra = math.degrees(math.atan2(x, z)) % 360
        dec = math.degrees(math.asin(y / math.dist(earth, moon)))
        self.assertAlmostEqual(ra, 15*(21+9/60+46/3600), delta=0.0021)
        self.assertAlmostEqual(dec, -(17+58/60+42/3600), delta=0.00014)

if __name__ == '__main__':
    unittest.main()
