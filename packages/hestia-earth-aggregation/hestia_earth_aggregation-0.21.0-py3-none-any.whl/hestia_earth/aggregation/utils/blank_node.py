import math
from typing import List
from functools import reduce, lru_cache
from hestia_earth.schema import SchemaType, TermTermType
from hestia_earth.utils.lookup import download_lookup, get_table_value, column_name, find_term_ids_by, lookup_term_ids
from hestia_earth.utils.tools import non_empty_list, flatten, list_sum, is_number, safe_parse_float
from hestia_earth.utils.model import find_term_match, linked_node
from hestia_earth.utils.blank_node import ArrayTreatment, get_node_value, _retrieve_array_treatment
from hestia_earth.utils.term import download_term

from hestia_earth.aggregation.log import logger
from . import pick, match_dates
from .term import DRY_MATTER_TERM_ID, term_dryMatter
from .management import aggregated_dates

_GROUP_KEYS_100 = [
    'sumMax100Group',
    'sumIs100Group'
]
# groups that need to be present event if no blank nodes are found
_MANDATORY_GROUPS = {
    TermTermType.STANDARDSLABELS.value: SchemaType.PRACTICE.value,
    TermTermType.SYSTEM.value: SchemaType.PRACTICE.value,
}


def _blank_node_type(blank_node: dict): return blank_node.get('@type') or blank_node.get('type')


def get_lookup_value(lookup_term: dict, column: str):
    table_name = f"{lookup_term.get('termType')}.csv" if lookup_term else None
    return get_table_value(
        download_lookup(table_name), 'termid', lookup_term.get('@id'), column_name(column)
    ) if table_name else None


@lru_cache()
def _default_value(term_id: str, term_type: str):
    return _parse_default_value(get_lookup_value({'@id': term_id, 'termType': term_type}, 'aggregatedDefaultValue'))


def _formatDepth(depth: str):
    # handle float values
    return str(int(depth)) if is_number(depth) else ''


def _parse_default_value(value):
    return (
        True if str(value).lower() == 'true' else
        False if str(value).lower() == 'false' else
        safe_parse_float(value, default=None)
    ) if value is not None else None


def _default_value_term_ids_map(term_type: str):
    lookup = download_lookup(f"{term_type}.csv")
    values = {
        term_id: _default_value(term_id, term_type)
        for term_id in lookup_term_ids(lookup)
    }
    return {k: v for k, v in values.items() if v is not None}


def default_missing_value(term: dict):
    default_value = _default_value(term['@id'], term['termType'])
    # value can be string, number or boolean
    # use lookup `valueType` to determine which value to add
    return (
        default_value if default_value is not None else
        {'boolean': False}.get(get_lookup_value(term, 'valueType'), 0)
    )


def _node_dryMatter(blank_node: dict):
    return safe_parse_float(find_term_match(blank_node.get('properties', []), DRY_MATTER_TERM_ID).get('value'))


def node_dryMatter_rescale_ratio(blank_node: dict):
    """
    Return the rescale ratio between the user provided `dryMatter` and HESTIA default `dryMatter`.
    """
    # for products with the `dryMatter` property, need to rescale using our default value
    node_dm = _node_dryMatter(blank_node)
    default_dm = term_dryMatter(blank_node.get('term', {})) if node_dm else 0
    return node_dm / default_dm if all([node_dm, default_dm]) else 1


def _blank_node_dates(blank_node: dict):
    node_type = _blank_node_type(blank_node)
    return aggregated_dates(blank_node) if node_type == SchemaType.MANAGEMENT.value else (
        pick(blank_node, ['startDate', 'endDate'])
    )


def _properties_group(blank_node: dict):
    properties = [p for p in blank_node.get('properties', []) if should_aggregate_blank_node(p)]
    group_key = '-'.join(non_empty_list([
        get_lookup_value(prop.get('term'), 'blankNodesGroup') or prop.get('term', {}).get('@id')
        for prop in properties
    ]))
    return group_key


def _default_blank_node_group_key(blank_node: dict, include_dates: bool = True):
    node_type = _blank_node_type(blank_node)
    keys = non_empty_list(flatten([
        _formatDepth(blank_node.get('depthUpper')),
        _formatDepth(blank_node.get('depthLower')),
        blank_node.get('startDate') if include_dates else '',
        blank_node.get('endDate') if include_dates else '',
        [v.get('@id') for v in blank_node.get('inputs', [])] if node_type == SchemaType.EMISSION.value else '',
        _properties_group(blank_node)
    ]))
    return '-'.join(keys)


def blank_node_group_key(blank_node: dict):
    keys = non_empty_list([
        _default_blank_node_group_key(blank_node, include_dates=_blank_node_type(blank_node) in [
            SchemaType.MANAGEMENT.value,
            SchemaType.MEASUREMENT.value,
        ]),
        blank_node.get('term', {}).get('@id')
    ])
    return '-'.join(keys)


def group_by_term_id(group: dict, node: dict):
    group_key = blank_node_group_key(node)
    group[group_key] = group.get(group_key, []) + [node]
    return group


def _group_blank_nodes(nodes: list):
    """
    Group a list of blank nodes using:
    - `termType`
    - the `depthUpper` and `depthLower`
    - the `startDate` and `endDate`
    - the lookup group `sumMax100Group` or `sumIs100Group` or `booleanGroup` if specified

    Parameters
    ----------
    nodes : list
        List of blank nodes with their index.
    """
    def group_by(group: dict, blank_node: dict):
        term = blank_node.get('term', {})
        term_type = term.get('termType')
        lookup = download_lookup(f"{term_type}.csv")
        sum_below_100_group = get_table_value(lookup, 'termid', term.get('@id'), column_name('sumMax100Group')) \
            if lookup is not None else None
        sum_equal_100_group = get_table_value(lookup, 'termid', term.get('@id'), column_name('sumIs100Group')) \
            if lookup is not None else None
        boolean_group = get_table_value(lookup, 'termid', term.get('@id'), column_name('booleanGroup')) \
            if lookup is not None else None

        keys = non_empty_list([
            _default_blank_node_group_key(blank_node),
            term_type,
            sum_below_100_group,
            sum_equal_100_group,
            boolean_group
        ])
        key = '-'.join(keys)

        group[key] = group.get(key, []) + [{
            'key': key,
            'node': blank_node,
            'sumMax100Group': sum_below_100_group,
            'sumIs100Group': sum_equal_100_group,
            'booleanGroup': boolean_group
        }]

        return group

    return reduce(group_by, nodes, {})


def _filter_by_array_treatment(blank_node: dict):
    term = blank_node.get('term', {})
    lookup = download_lookup(f"{term.get('termType')}.csv")
    value = get_table_value(lookup, 'termid', term.get('@id'), column_name('arrayTreatmentLargerUnitOfTime'))
    # ignore any blank node with time-split data
    return not value


def _filter_needs_depth(blank_node: dict):
    term = blank_node.get('term', {})
    lookup = download_lookup(f"{term.get('termType')}.csv")
    needs_depth = get_table_value(lookup, 'termid', term.get('@id'), column_name('recommendAddingDepth'))
    return not needs_depth or all([blank_node.get('depthUpper') is not None, blank_node.get('depthLower') is not None])


def _missing_blank_node(blank_node: dict, term_id: str):
    term = linked_node(download_term(term_id, blank_node['term']['termType']))
    value = default_missing_value(term)
    return {
        '@type': _blank_node_type(blank_node),
        'term': term,
        'value': [value]
    }


def _missing_term_ids_by_group(blank_nodes: List[dict], lookup_group_key: str):
    blank_node = blank_nodes[0].get('node')
    term = blank_node.get('term', {})
    term_type = term.get('termType')
    lookup = download_lookup(f"{term_type}.csv")
    group_id = blank_nodes[0].get(lookup_group_key)
    term_ids = find_term_ids_by(lookup, column_name(lookup_group_key), group_id)
    existing_ids = [v.get('node').get('term', {}).get('@id') for v in blank_nodes]
    return [term_id for term_id in term_ids if term_id not in existing_ids]


def _missing_term_ids_by_termType(blank_nodes: List[dict]):
    blank_node = blank_nodes[0].get('node')
    term = blank_node.get('term', {})
    term_type = term.get('termType')
    term_ids = list(_default_value_term_ids_map(term_type).keys())
    existing_ids = [v.get('node').get('term', {}).get('@id') for v in blank_nodes] if term_ids else []
    return [term_id for term_id in term_ids if term_id not in existing_ids]


def _filter_grouped_nodes(blank_nodes: List[dict]):
    values = flatten([v.get('node').get('value', []) for v in blank_nodes])
    total_value = list_sum(values)
    is_100_total = 99.5 <= total_value <= 100.5
    blank_node = blank_nodes[0]

    group_key_100 = next((k for k in _GROUP_KEYS_100 if blank_node.get(k)), None)
    # only use 100 group if the total is 100% as otherwise we can not validate to 100%
    is_group_key_100_valid = all([group_key_100, is_100_total])
    if all([group_key_100, not is_100_total, total_value > 0]):
        logger.debug('Sum of group %s equal to %s, skipping.', blank_node.get('key'), total_value)

    missing_term_ids = (
        _missing_term_ids_by_group(blank_nodes, group_key_100) if is_group_key_100_valid else
        _missing_term_ids_by_termType(blank_nodes)
    )

    blank_node = blank_node.get('node')
    dates = _blank_node_dates(blank_node)
    return [
        r | dates
        for r in (
            [v.get('node') for v in blank_nodes] + [
                _missing_blank_node(blank_node, term_id) | pick(blank_node, [
                    'startDate', 'endDate', 'properties'
                ])
                for term_id in missing_term_ids
            ]
        )
    ] if not group_key_100 or is_group_key_100_valid else []


def node_type_allowed(term: dict, node_type: str):
    lookup = download_lookup(f"{term.get('termType')}.csv")
    values = get_table_value(lookup, 'termid', term.get('@id'), column_name('skipAggregatedNodeTypes'))
    skipped_values = values.split(';') if values and isinstance(values, str) else []
    return 'all' not in skipped_values and node_type not in skipped_values


def should_aggregate_blank_node(blank_node: dict):
    term = blank_node.get('term', {})
    node_type = _blank_node_type(blank_node)
    return node_type_allowed(term, node_type)


def _missing_grouped_nodes(term_type: str):
    # add blank nodes in empty groups
    node_type = _MANDATORY_GROUPS.get(term_type)
    missing_term_ids_map = _default_value_term_ids_map(term_type) if node_type else []
    return [
        {
            '@type': _MANDATORY_GROUPS.get(term_type),
            'term': linked_node(download_term(term_id, term_type)),
            'value': [value]
        }
        for term_id, value in missing_term_ids_map.items()
    ]


def filter_blank_nodes(
    blank_nodes: List[dict], start_year: int = None, end_year: int = None, include_mandatory_groups: bool = False
):
    nodes = [v for v in blank_nodes if all([
        should_aggregate_blank_node(v),
        _filter_by_array_treatment(v),
        # _filter_needs_depth(v),  # allow measurements without depths to be aggregated together
        not start_year or not end_year or match_dates(v, start_year, end_year),
        # ignore `Management` node with grouped `properties` as creating conflicts over same `tern`
        _blank_node_type(v) != SchemaType.MANAGEMENT.value or not _properties_group(v)
    ])]

    grouped_values = (
        {termType: [] for termType in _MANDATORY_GROUPS.keys()} if include_mandatory_groups else {}
    ) | _group_blank_nodes(nodes)
    return flatten([
        # handle no blank nodes in the group, see mandatory groups above
        _missing_grouped_nodes(key) if not values else _filter_grouped_nodes(values)
        for key, values in grouped_values.items()
    ])


def _is_value_zero(value):
    return value == [0] if isinstance(value, list) else (value == 0 or value == 0.0) if value is not None else False


def _remove_value_zero(blank_node: dict):
    term = blank_node.get('term', {})
    return all([
        term.get('units') == '% area',
        _is_value_zero(blank_node.get('value'))
    ]) and (
        any([bool(get_lookup_value(term, key)) for key in _GROUP_KEYS_100]) or
        get_node_value(blank_node) == _default_value(term['@id'], term['termType'])
    )


def cleanup_blank_nodes(blank_nodes: List[dict]):
    # remove all blank nodes with `0` as value to reduce the node count
    return list(filter(lambda v: not _remove_value_zero(v), non_empty_list(blank_nodes)))


def _rescale_product_value_dm(node: dict, value: float):
    # for products with the `dryMatter` property, need to rescale using our default value
    rescale_ratio = node_dryMatter_rescale_ratio(node)
    return value * rescale_ratio


def _blank_node_value(blank_node: dict, complete: bool, is_aggregated_product: bool):
    """
    Handle completeness for `value` field.
    Rules:
    - if the blank_node is complete, use the value or set `0` if no value
    - if the blank_node is incomplete:
      - if it is the aggregated product, use the value
      - otherwise, do not use the value
    """
    default_value = default_missing_value(blank_node.get('term')) if complete else None
    value = get_node_value(blank_node, 'value', default=default_value)
    is_product = _blank_node_type(blank_node) == SchemaType.PRODUCT.value

    return (
        _rescale_product_value_dm(blank_node, value) if all([
            is_product,
            value
        ]) else value
    ) if complete is not False else (
        value if is_aggregated_product else None
    )


def _blank_node_evs(blank_node: dict, complete: bool, is_aggregated_product: bool):
    """
    Handle product evs.
    Only use the evs if the primary product is complete or has a value.
    """
    return blank_node.get('economicValueShare') if all([
        is_aggregated_product,
        complete or get_node_value(blank_node, 'value', default=0) != 0
    ]) else None


def _default_sd(value: dict, array_treatment: ArrayTreatment):
    min_value = get_node_value(value, key='min', array_treatment=array_treatment, default=None)
    max_value = get_node_value(value, key='max', array_treatment=array_treatment, default=None)
    return [(max_value-min_value)/4] if all([min_value, max_value]) else None


def blank_node_sd(blank_node: dict, array_treatment: ArrayTreatment):
    value = blank_node.get('sd') or _default_sd(blank_node, array_treatment)
    value = non_empty_list(value if isinstance(value, list) else [value])
    sd = math.sqrt(sum([v**2 for v in value])) if value else None
    return (
        sd / len(value) if array_treatment == ArrayTreatment.MEAN else sd
    ) if value else None


def map_blank_node(blank_node: dict, is_aggregated_product: bool = False):
    """
    Simplify blank node data by only keeping what we use in aggregation.
    """
    complete = blank_node.get('complete')
    value = _blank_node_value(blank_node, complete, is_aggregated_product)
    is_primary = blank_node.get('primary', False) or is_aggregated_product
    array_treatment = _retrieve_array_treatment(blank_node, default=ArrayTreatment.SUM)
    return blank_node | {
        'primary': is_primary,
        'value': value,
        'economicValueShare': _blank_node_evs(blank_node, complete, is_aggregated_product),
        'min': get_node_value(blank_node, 'min', default=None),
        'max': get_node_value(blank_node, 'max', default=None),
        'sd': blank_node_sd(blank_node, array_treatment),
        'observations': 0 if value is None else 1,
        'properties': [
            pick(p, ['term', 'value'])
            for p in blank_node.get('properties', [])
            if should_aggregate_blank_node(p)
        ]
    }
