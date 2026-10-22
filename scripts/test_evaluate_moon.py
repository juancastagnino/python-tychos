import copy
import unittest
from datetime import datetime
import tychos
from evaluate_moon import evaluate, validate

class LunarEvaluatorTests(unittest.TestCase):
    def test_baseline_matches_existing_positions(self):
        config = copy.deepcopy(tychos.LUNAR_DEFAULTS)
        self.assertEqual(tychos.positions(tychos.EPOCH), tychos.positions(tychos.EPOCH, validate(config)))
        config['orbit']['radius'] += 0.01
        self.assertNotEqual(tychos.positions(tychos.EPOCH)[1], tychos.positions(tychos.EPOCH, config)[1])

    def test_invalid_and_unknown_parameters_rejected(self):
        config = copy.deepcopy(tychos.LUNAR_DEFAULTS)
        config['orbit']['radius'] = float('nan')
        with self.assertRaises(ValueError): validate(config)
        config = copy.deepcopy(tychos.LUNAR_DEFAULTS)
        config['node']['extra'] = 1
        with self.assertRaises(ValueError): validate(config)

    def test_splits_include_boundaries_and_empty_groups(self):
        reference = {('Moon', datetime(2000,1,1)): (0,0,380000), ('Moon', datetime(2011,1,1)): (0,0,380000)}
        result = evaluate(tychos.LUNAR_DEFAULTS, reference)
        self.assertEqual(result['train']['sample_count'], 1)
        self.assertEqual(result['validation']['sample_count'], 1)
        self.assertIsNone(result['historical']['metrics'])

if __name__ == '__main__': unittest.main()
