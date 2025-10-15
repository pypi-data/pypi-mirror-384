def validate_quality_score_min(node: dict, max_diff: int = 2):
    node_id = node.get('@id', node.get('id', ''))
    key = 'aggregatedQualityScore'
    value = node.get(key, 0)
    max_value = node.get(key + 'Max', 0)
    min_value = max_value - max_diff
    # ignore nodes that are organic or irrigated as they should not block the upload of other nodes
    level = 'warning' if any(['organic' in node_id, 'irrigated' in node_id]) else 'error'
    return value >= min_value or {
        'level': level,
        'dataPath': f".{key}",
        'message': f"must be at least equal to {min_value}",
        'params': {
            'expected': min_value,
            'current': value,
            'min': min_value,
            'max': max_value
        }
    }


def validate_id(node: dict):
    # make sure the ID contains a product ID, region ID, start and end year
    node_id = node.get('id', '')
    # there should be 4 different components to the id
    node_id_length = len(node_id.split('-'))
    return not node_id or node_id_length >= 4 or {
        'level': 'error',
        'dataPath': '.id',
        'message': 'aggregation id must contain a product, region, start, and end year'
    }
