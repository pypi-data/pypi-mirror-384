import logging
import os

LOGGER = logging.getLogger(__name__)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG') # Default to DEBUG if not set
LOGGER.setLevel(LOG_LEVEL)
LOGGER.info(f'🔄 {__name__} Setting logger level to {LOG_LEVEL}...')

LOGS_TO_HIDE = [
    'PIL',
]
for logger_name in LOGS_TO_HIDE:
    logging.getLogger(logger_name).setLevel(logging.INFO)
    LOGGER.info(f'🔕 {logger_name} logger set to INFO level to reduce verbosity...')
