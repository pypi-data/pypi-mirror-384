import pytest

from hestia_earth.validation.utils import match_value_type


@pytest.mark.parametrize(
    'value,value_type,is_valid',
    [
        (10, 'number', True),
        (True, 'number', False),
        ([10, 20], 'number', True),
        ([10, True], 'number', False),
        ([True, False], 'boolean', True),
        (True, 'boolean', True),
        ([10, 20], 'boolean', False),
    ]
)
def test_match_value_type(value, value_type: str, is_valid: bool):
    assert match_value_type(value_type, value) == is_valid, value
