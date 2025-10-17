import os
from typing import List, Tuple
from hestia_earth.utils.stats import truncated_normal_1d
from hestia_earth.utils.tools import flatten, to_precision
import random
import numpy as np

from . import _all_boolean
from .blank_node import get_lookup_value


def _nb_iterations(): return int(os.getenv('AGGREGATION_DISTRIBUTION_SIZE', '1000'))


def _sample_values(values: List[float], nb_iterations: int = None):
    return random.sample(values, nb_iterations or _nb_iterations())


def _sample_indexes(values: list): return [random.sample(range(len(values)), 1)[0] for _ in range(_nb_iterations())]


def _distribute_iterations(values: list, iterations: int = None):
    iterations = iterations or _nb_iterations()
    num_iterations = int(iterations / len(values))
    total_iterations = len(values) * num_iterations
    remaining_iterations = iterations - total_iterations
    return [num_iterations + 1] * remaining_iterations + [num_iterations] * (len(values) - remaining_iterations)


def generate_distribution(
    term: dict, *_, value: float, min: float = None, max: float = None, sd: float = None, iterations: int = None
):
    iterations = iterations or _nb_iterations()
    has_min_value = all([min is not None, value is not None]) and min < value
    min_bound = min if has_min_value else get_lookup_value(term, 'minimum')
    min_bound = -np.inf if min_bound is None else min_bound

    has_max_value = all([max is not None, value is not None]) and max > value
    max_bound = max if has_max_value else get_lookup_value(term, 'maximum')
    max_bound = np.inf if max_bound is None else max_bound

    result = [] if isinstance(value, bool) else list(
        (
            truncated_normal_1d(shape=(1, iterations), mu=value, sigma=sd or (max-min)/4, low=min, high=max) if all([
                has_min_value,
                has_max_value
            ]) else
            truncated_normal_1d(shape=(1, iterations), mu=value, sigma=sd, low=min_bound, high=max_bound) if all([
                sd is not None
            ]) else
            [[value] * iterations]
        )[0]
    ) if value is not None else []
    return [(to_precision(v) if v > 0 else v) for v in result]


def _generate_blank_node_distribution_random_iterations(blank_node: dict):
    # generate distribution, by using random indexes
    # this method is only called when the number of values is greater than the number of iterations
    value = blank_node.get('value', [])
    random_indexes = _sample_indexes(value)

    def _value_at_index(index: int, key: str):
        values = blank_node.get(key) or []
        try:
            return values[index]
        # TODO catch only IndexError, and figure out why `sd` is a float instead of a list
        except Exception:
            return None

    return flatten([
        generate_distribution(
            term=blank_node['term'],
            value=_value_at_index(index, 'value'),
            min=_value_at_index(index, 'min'),
            max=_value_at_index(index, 'max'),
            sd=_value_at_index(index, 'sd'),
            iterations=1
        )
        for index in random_indexes
    ])


def _generate_blank_node_distribution_distributed_iterations(blank_node: dict):
    # generate distributions equally distributed across the different values
    # this method is only called when the number of values is smaller than the number of iterations
    value = blank_node.get('value', [])

    def _value_at_index(index: int, key: str):
        values = blank_node.get(key) or []
        try:
            return values[index]
        # TODO catch only IndexError, and figure out why `sd` is a float instead of a list
        except Exception:
            return None

    iterations = _distribute_iterations(value)

    return flatten([
        generate_distribution(
            term=blank_node['term'],
            value=_value_at_index(index, 'value'),
            min=_value_at_index(index, 'min'),
            max=_value_at_index(index, 'max'),
            sd=_value_at_index(index, 'sd'),
            iterations=iterations[index]
        )
        for index in range(0, len(value))
    ])


def generate_blank_node_distribution(blank_node: dict):
    total_iterations = _nb_iterations()
    value = blank_node.get('value', [])
    return (
        _generate_blank_node_distribution_random_iterations(blank_node) if len(value) >= total_iterations else
        _generate_blank_node_distribution_distributed_iterations(blank_node)
    ) if len(value) > 0 and total_iterations > 0 else []


def sample_distributions(
    distributions: List[List[float]],
    total_iterations: int = None,
    iteration_ratio: float = 1.0
):
    total_iterations = total_iterations or _nb_iterations()
    values = flatten(distributions)
    nb_iterations = round(total_iterations * iteration_ratio)
    return (
        [] if _all_boolean(values) else
        values if len(values) <= nb_iterations else
        _sample_values(values, nb_iterations)
    ) if len(values) > 0 and total_iterations > 0 else []


def sample_weighted_distributions(distributions: List[Tuple[List[float], float]], total_iterations: int = None):
    total_iterations = total_iterations or _nb_iterations()
    weighted_distributions = [
        sample_distributions(value, total_iterations=total_iterations, iteration_ratio=weight)
        for value, weight in distributions
    ]
    values = flatten(weighted_distributions)
    missing_iterations = total_iterations - len(values)
    missing_values = (
        # account for rounding errors
        sample_distributions([v for v, w in distributions], missing_iterations) if missing_iterations > 0 else []
    )
    return values + missing_values
