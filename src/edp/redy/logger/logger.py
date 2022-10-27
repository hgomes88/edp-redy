import logging.config
import os

LOGGER_CONF = os.path.dirname(__file__) + '/logger.conf'

print(LOGGER_CONF)
logging.config.fileConfig(LOGGER_CONF)
