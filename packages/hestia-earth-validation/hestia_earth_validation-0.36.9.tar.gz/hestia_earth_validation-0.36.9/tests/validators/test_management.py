import os
import json
from hestia_earth.schema import TermTermType

from tests.utils import fixtures_path
from hestia_earth.validation.validators.management import (
    validate_has_termType,
    validate_has_termTypes,
    validate_exists,
    validate_fallow_dates,
    validate_cycles_overlap
)

fixtures_folder = os.path.join(fixtures_path, 'management')


def test_validate_has_termType_valid():
    with open(f"{fixtures_folder}/termType/valid-cropland.json") as f:
        site = json.load(f)

    assert validate_has_termType(site, TermTermType.LANDUSEMANAGEMENT) is True

    with open(f"{fixtures_folder}/termType/valid-permanent-pasture.json") as f:
        site = json.load(f)

    assert validate_has_termType(site, TermTermType.LANDUSEMANAGEMENT) is True


def test_validate_has_termType_invalid():
    with open(f"{fixtures_folder}/termType/invalid-cropland.json") as f:
        site = json.load(f)

    assert validate_has_termType(site, TermTermType.LANDUSEMANAGEMENT) == {
        'level': 'warning',
        'dataPath': '.management',
        'message': 'should contain at least one management node',
        'params': {
            'termType': 'landUseManagement'
        }
    }

    with open(f"{fixtures_folder}/termType/invalid-permanent-pasture.json") as f:
        site = json.load(f)

    assert validate_has_termType(site, TermTermType.WATERREGIME) == {
        'level': 'warning',
        'dataPath': '.management',
        'message': 'should contain at least one management node',
        'params': {
            'termType': 'waterRegime'
        }
    }


def test_validate_has_termTypes_valid():
    # no blank node is valid
    site = {}
    assert validate_has_termTypes(site) is True

    with open(f"{fixtures_folder}/termType/valid-cropland.json") as f:
        site = json.load(f)

    assert validate_has_termTypes(site) is True

    with open(f"{fixtures_folder}/termType/valid-permanent-pasture.json") as f:
        site = json.load(f)

    assert validate_has_termTypes(site) is True

    with open(f"{fixtures_folder}/termType/valid-no-management.json") as f:
        site = json.load(f)

    assert validate_has_termTypes(site) is True


def test_validate_has_termTypes_invalid():
    with open(f"{fixtures_folder}/termType/invalid-cropland.json") as f:
        site = json.load(f)

    assert validate_has_termTypes(site) == [
        {
            'level': 'warning',
            'dataPath': '.management',
            'message': 'should contain at least one management node',
            'params': {
                'termType': 'landUseManagement'
            }
        },
        {
            'level': 'warning',
            'dataPath': '.management',
            'message': 'should contain at least one management node',
            'params': {
                'termType': 'waterRegime'
            }
        }
    ]

    with open(f"{fixtures_folder}/termType/invalid-permanent-pasture.json") as f:
        site = json.load(f)

    assert validate_has_termTypes(site) == [
        {
            'level': 'warning',
            'dataPath': '.management',
            'message': 'should contain at least one management node',
            'params': {
                'termType': 'landUseManagement'
            }
        },
        {
            'level': 'warning',
            'dataPath': '.management',
            'message': 'should contain at least one management node',
            'params': {
                'termType': 'waterRegime'
            }
        }
    ]


def test_validate_exists_valid():
    with open(f"{fixtures_folder}/exists/valid.json") as f:
        site = json.load(f)

    assert validate_exists(site) is True


def test_validate_exists_invalid():
    with open(f"{fixtures_folder}/exists/invalid.json") as f:
        site = json.load(f)

    assert validate_exists(site) == {
        'level': 'warning',
        'dataPath': '.management',
        'message': 'should contain at least one management node'
    }


def test_validate_defaultValue_valid():
    # no management should be valid
    assert validate_fallow_dates({}) is True

    with open(f"{fixtures_folder}/fallow-dates/valid.json") as f:
        data = json.load(f)
    assert validate_fallow_dates(data, 'management') is True


def test_validate_defaultValue_invalid():
    with open(f"{fixtures_folder}/fallow-dates/invalid.json") as f:
        data = json.load(f)
    assert validate_fallow_dates(data, 'management') == {
        'level': 'error',
        'dataPath': '.management[0]',
        'message': 'duration must be in specified interval',
        'params': {
            'term': {
                '@type': 'Term',
                '@id': 'shortFallow'
            },
            'current': 730,
            'expected': 'less-than-1-year'
        }
    }


def test_validate_cycles_overlap_valid():
    # no management should be valid
    assert validate_cycles_overlap({}, []) is True

    with open(f"{fixtures_folder}/cycle-overlap/cycles.json") as f:
        cycles = json.load(f)

    with open(f"{fixtures_folder}/cycle-overlap/valid.json") as f:
        data = json.load(f)
    # no cycles should be valid
    assert validate_cycles_overlap(data, cycles=[]) is True
    assert validate_cycles_overlap(data, cycles, 'management') is True


def test_validate_cycles_overlap_invalid():
    with open(f"{fixtures_folder}/cycle-overlap/cycles.json") as f:
        cycles = json.load(f)

    with open(f"{fixtures_folder}/cycle-overlap/invalid.json") as f:
        data = json.load(f)
    assert validate_cycles_overlap(data, cycles, 'management') == {
        'level': 'error',
        'dataPath': '.management[0].endDate',
        'message': 'must be before 2020-03-12'
    }
