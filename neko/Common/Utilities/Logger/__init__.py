# -*- encoding: UTF-8 -*-


import logging

from neko.Configuration import LOGGER_CONFIGURATION
from .ConsoleLogger import ConsoleLogger
from .FileLogger import FileLogger

logger = logging.getLogger(LOGGER_CONFIGURATION["LOGGER_NAME"])
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt = LOGGER_CONFIGURATION["LOGGER_FORMAT"],
    datefmt = LOGGER_CONFIGURATION["LOGGER_DATE_FORMAT"]
)

if LOGGER_CONFIGURATION["ENABLE_CONSOLE_LOGGER"]:
    console_logger = ConsoleLogger(
        use_colors = LOGGER_CONFIGURATION["CONSOLE_LOGGER_USE_COLORS"]
    )
    console_logger.setFormatter(formatter)
    console_logger.setLevel(LOGGER_CONFIGURATION["CONSOLE_LOGGER_LEVEL"])
    logger.addHandler(console_logger)

if LOGGER_CONFIGURATION["ENABLE_FILE_LOGGER"]:
    file_logger = FileLogger(
        file_name = LOGGER_CONFIGURATION["FILE_LOGGER_FILE_NAME"],
        file_max_size = LOGGER_CONFIGURATION["FILE_LOGGER_FILE_MAX_SIZE"],
        file_encoding = LOGGER_CONFIGURATION["FILE_LOGGER_FILE_ENCODING"],
        file_backup_count = LOGGER_CONFIGURATION["FILE_LOGGER_FILE_BACKUP_COUNT"]
    )
    file_logger.setFormatter(formatter)
    file_logger.setLevel(LOGGER_CONFIGURATION["FILE_LOGGER_LEVEL"])
    logger.addHandler(file_logger)
