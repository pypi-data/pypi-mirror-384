from hestia_earth.schema import TermTermType, SiteSiteType
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.tools import flatten, safe_parse_date
from hestia_earth.utils.date import diff_in_days

from hestia_earth.validation.utils import _filter_list_errors, cycle_start_date

_SITE_TYPE_TO_TERM_TYPES = {
    SiteSiteType.CROPLAND.value: [
        TermTermType.CROPRESIDUEMANAGEMENT,
        TermTermType.LANDUSEMANAGEMENT,
        TermTermType.TILLAGE,
        TermTermType.WATERREGIME
    ],
    SiteSiteType.PERMANENT_PASTURE.value: [
        TermTermType.LANDUSEMANAGEMENT,
        TermTermType.WATERREGIME
    ]
}


def validate_has_termType(site: dict, term_type: TermTermType):
    blank_nodes = filter_list_term_type(site.get('management', []), term_type)
    return len(blank_nodes) > 0 or {
        'level': 'warning',
        'dataPath': '.management',
        'message': 'should contain at least one management node',
        'params': {
            'termType': term_type.value
        }
    }


def validate_has_termTypes(site: dict):
    blank_nodes = site.get('management', [])
    term_types = _SITE_TYPE_TO_TERM_TYPES.get(site.get('siteType'), [])
    return len(term_types) == 0 or len(blank_nodes) == 0 or _filter_list_errors([
        validate_has_termType(site, term_type) for term_type in term_types
    ])


def validate_exists(site: dict):
    blank_nodes = site.get('management', [])
    term_types = _SITE_TYPE_TO_TERM_TYPES.get(site.get('siteType'), [])
    return len(term_types) == 0 or len(blank_nodes) > 0 or {
        'level': 'warning',
        'dataPath': '.management',
        'message': 'should contain at least one management node'
    }


_FALLOW_DATE_VALID_FUNC = {
    'less-than-1-year': lambda days: days <= 365,
    'between-1-and-5-years': lambda days: 365 < days <= 365.25*5,
    'less-than-20-years': lambda days: days <= 365.25*20,
    '': lambda *args: True
}


_FALLOW_DATE_VALID_TERM_TO_KEY = {
    'shortFallow': 'less-than-1-year',
    'shortBareFallow': 'less-than-1-year',
    'longFallow': 'between-1-and-5-years',
    'longBareFallow': 'between-1-and-5-years',
    'setAside': 'less-than-20-years'
}


def validate_fallow_dates(data: dict, list_key: str = 'management'):
    def validate(values: tuple):
        index, blank_node = values
        term = blank_node.get('term', {})
        term_id = term.get('@id')
        start_date = blank_node.get('startDate')
        end_date = blank_node.get('endDate')
        days = diff_in_days(start_date, end_date) if all([start_date, end_date]) else None
        validation_key = _FALLOW_DATE_VALID_TERM_TO_KEY.get(term_id, '')
        return days is None or _FALLOW_DATE_VALID_FUNC.get(validation_key)(days) or {
            'level': 'error',
            'dataPath': f".{list_key}[{index}]",
            'message': 'duration must be in specified interval',
            'params': {
                'term': term,
                'current': days,
                'expected': validation_key
            }
        }

    return _filter_list_errors(flatten(map(validate, enumerate(data.get(list_key, [])))))


def validate_cycles_overlap(data: dict, cycles: list, list_key: str = 'management'):
    """
    Prevent overlap between management dates and cycle dates.
    """
    first_cycle = sorted(cycles, key=lambda v: v.get('endDate'))[0] if cycles else None
    earliest_start_date = cycle_start_date(first_cycle) if first_cycle else None
    earliest_start_date_str = earliest_start_date.strftime('%Y-%m-%d') if earliest_start_date else None

    def validate(values: tuple):
        index, blank_node = values
        end_date = blank_node.get('endDate')
        return not end_date or safe_parse_date(end_date) < earliest_start_date or {
            'level': 'error',
            'dataPath': f".{list_key}[{index}].endDate",
            'message': f"must be before {earliest_start_date_str}"
        }

    return not earliest_start_date or _filter_list_errors(flatten(map(validate, enumerate(data.get(list_key, [])))))
