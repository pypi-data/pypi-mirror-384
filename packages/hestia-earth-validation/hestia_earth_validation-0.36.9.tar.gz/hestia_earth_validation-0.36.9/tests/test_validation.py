from unittest.mock import patch

from hestia_earth.validation import validate


@patch('hestia_earth.validation.init_gee_by_nodes')
@patch('hestia_earth.validation.validate_node')
def test_validate_call_validate_node(mock_validate_node, *args):
    node = {'type': 'Site'}
    validate([node])
    mock_validate_node.assert_called_once()
