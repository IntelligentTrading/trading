import os
import logging
import webserver.settings
import init_django  # noqa


def get_level():
    lvl = os.environ.get("LOGGING_LEVEL")
    if lvl is not None:
        return logging._nameToLevel[lvl]
    return logging.DEBUG


logging.config.dictConfig(webserver.settings.LOGGING)
logger = logging.getLogger('main')
logger.setLevel(get_level())
