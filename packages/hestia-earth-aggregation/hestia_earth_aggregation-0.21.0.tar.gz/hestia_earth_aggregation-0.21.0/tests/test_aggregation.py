from unittest.mock import Mock, patch

from hestia_earth.aggregation import aggregate

class_path = 'hestia_earth.aggregation'


@patch(f"{class_path}.run_aggregate", return_value=([], []))
def test_aggregate(mock_aggregate: Mock):
    aggregate({}, {}, 2000, 2009, {})
    mock_aggregate.assert_called_once()
