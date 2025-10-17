from hestia_earth.validation.validators.aggregated_shared import (
    validate_quality_score_min,
    validate_id
)


def test_validate_quality_score_min_valid():
    assert validate_quality_score_min({}) is True

    node = {
        'id': 'wheatGrain-united-kingdom-2000-2009',
        'aggregatedQualityScore': 3,
        'aggregatedQualityScoreMax': 5
    }
    assert validate_quality_score_min(node) is True

    node = {
        'id': 'wheatGrain-united-kingdom-2000-2009',
        'aggregatedQualityScore': 5,
        'aggregatedQualityScoreMax': 5
    }
    assert validate_quality_score_min(node) is True


def test_validate_quality_score_min_error():
    node = {
        'id': 'wheatGrain-united-kingdom-2000-2009',
        'aggregatedQualityScore': 2,
        'aggregatedQualityScoreMax': 5
    }
    assert validate_quality_score_min(node) == {
        'level': 'error',
        'dataPath': '.aggregatedQualityScore',
        'message': 'must be at least equal to 3',
        'params': {
            'expected': 3,
            'current': 2,
            'min': 3,
            'max': 5
        }
    }


def test_validate_quality_score_min_warning():
    node = {
        'id': 'wheatGrain-united-kingdom-organic-non-irrigated-2000-2009',
        'aggregatedQualityScore': 2,
        'aggregatedQualityScoreMax': 5
    }
    assert validate_quality_score_min(node) == {
        'level': 'warning',
        'dataPath': '.aggregatedQualityScore',
        'message': 'must be at least equal to 3',
        'params': {
            'expected': 3,
            'current': 2,
            'min': 3,
            'max': 5
        }
    }


def test_validate_id_valid():
    assert validate_id({'id': 'sugarBeetRoot-region-world-2010-2025'}) is True
    assert validate_id({'id': 'sugarBeetRoot-GADM-FRA-2010-2025'}) is True


def test_validate_id_invalid():
    assert validate_id({'id': 'sugarBeetRoot-2010-2025'}) == {
        'level': 'error',
        'dataPath': '.id',
        'message': 'aggregation id must contain a product, region, start, and end year'
    }
