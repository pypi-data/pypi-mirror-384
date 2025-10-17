from hestia_earth.utils.tools import current_time_ms

from .log import logger
from .aggregate_cycles import run_aggregate
from .recalculate_cycles import should_recalculate, recalculate
from .utils import distribution
from .utils.quality_score import calculate_score


def _mock_nb_distribution(include_distribution: bool):
    original_func = distribution._nb_iterations
    distribution._nb_iterations = lambda *args: original_func(*args) if include_distribution else 0
    not include_distribution and logger.warning('Not generating distribution.')


def aggregate(
    country: dict,
    product: dict,
    start_year: int,
    end_year: int,
    source: dict = None,
    include_distribution: bool = True,
    filter_by_country: bool = True
):
    """
    Aggregates data from HESTIA.
    Produced data will be aggregated by product, country and year.

    Parameters
    ----------
    country: dict
        The country to group the data.
    product: dict
        The product to group the data.
    start_year: int
        The start year of the data.
    end_year: int
        The end year of the data.
    source: dict
        Optional - the source of the generate data. Will be set to HESTIA if not provided.
    include_distribution : bool
        Include a `distribution` for each aggregated data point. Included by default.
    filter_by_country : bool
        If set to `False`, Cycles from all countries will be used.
        Only used for country-level aggregations.

    Returns
    -------
    list
        A list of aggregated Cycles with nested aggregated Sites.
    """
    # mock nb distributions depending on the parameter
    _mock_nb_distribution(include_distribution)

    now = current_time_ms()
    logger.info('Aggregating %s in %s for period %s to %s' + (' with distribution' if include_distribution else ''),
                product.get('name'),
                country.get('name'),
                start_year,
                end_year)
    aggregations, countries = run_aggregate(country, product, source, start_year, end_year, filter_by_country)
    logger.info('time=%s, unit=ms', current_time_ms() - now)
    aggregations = [
        recalculate(agg, product) for agg in aggregations
    ] if should_recalculate(product) else aggregations
    aggregations = [
        calculate_score(cycle=agg, countries=countries) for agg in aggregations
    ]
    return aggregations
