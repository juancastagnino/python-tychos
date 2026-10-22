"""Evaluate combinations of lunar parameters against the same baseline and JPL data."""
import copy
import itertools
import math

from evaluate_moon import validate
from sweep_moon import main


def combined_candidates(baseline, values):
    if not isinstance(values, dict) or not values:
        raise ValueError('Sweep values must be a non-empty object')
    names, choices = [], []
    for name, options in values.items():
        parts = name.split('.')
        if len(parts) != 2 or parts[0] not in baseline or parts[1] not in baseline[parts[0]]:
            raise ValueError(f'Unknown parameter: {name}')
        if not isinstance(options, list) or not options:
            raise ValueError(f'{name} must contain a non-empty array')
        unique = []
        for value in options:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'{name}: values must be finite numbers')
            if value not in unique:
                unique.append(value)
        names.append(name)
        choices.append(unique)

    result = [('baseline', None, None, copy.deepcopy(baseline))]
    for combination in itertools.product(*choices):
        config = copy.deepcopy(baseline)
        for name, value in zip(names, combination):
            section, field = name.split('.')
            config[section][field] = value
        if config == baseline:
            continue
        validate(config)
        # The existing CSV and Markdown reporter display the paired names and values.
        result.append((f'candidate_{len(result):03d}', '; '.join(names),
                       '; '.join(str(value) for value in combination), config))
    return result


if __name__ == '__main__':
    main(combined_candidates, 'scripts/combined_lunar_sweep_values.json')
