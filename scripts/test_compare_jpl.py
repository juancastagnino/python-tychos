import csv
import tempfile
import unittest
from pathlib import Path
from compare_jpl import angle, compare, read_horizons

class HorizonsTests(unittest.TestCase):
    def test_sexagesimal_negative_zero(self):
        self.assertAlmostEqual(angle('-00 30 00'), -0.5)
        self.assertAlmostEqual(angle('12 00 00', True), 180)

    def test_bundle_columns_matching_and_ra_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / 'jpl.txt'
            reference.write_text('# REQUEST BODY: moon\n Date__(UT)__HR:MN:SS, , , R.A._____(ICRF), DEC______(ICRF), R.A.____(a-app), DEC_____(a-app), delta, deldot,\n$$SOE\n2000-Jun-21 00:00:00, , , 23 59 59, +00 00 00, 00 00 00, -00 30 00, 0.0025, 0,\n$$EOE\n', encoding='utf-8')
            model = root / 'model.csv'
            with model.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['datetime_utc','body','ra_deg_native','dec_deg_native','distance_km'])
                writer.writerow(['2000-06-21T00:00:00+00:00','Moon','359.999','-0.5','373994.67675'])
            parsed = read_horizons(reference, 'apparent-of-date')
            stats, missing = compare(model, parsed)
            self.assertAlmostEqual(stats['Moon'][0][0], -0.001)
            self.assertAlmostEqual(stats['Moon'][0][1], 0)
            self.assertEqual(missing, {})
            self.assertGreater(next(iter(read_horizons(reference, 'icrf').values()))[0], 359)

if __name__ == '__main__':
    unittest.main()
