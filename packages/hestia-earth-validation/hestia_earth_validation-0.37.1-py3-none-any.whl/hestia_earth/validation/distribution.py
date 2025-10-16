import os
from functools import lru_cache

from .log import logger

ENABLED = os.getenv('VALIDATE_DISTRIBUTION', 'true') == 'true'


@lru_cache()
def is_enabled():
    if ENABLED:
        try:
            from hestia_earth.distribution.version import VERSION
            logger.debug("Using distribution version %s", VERSION)
            return True
        except ImportError:
            logger.error("Run `pip install hestia-earth-validation[distribution]` to use distribution validation")

    return False
