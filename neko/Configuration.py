# -*- encoding: UTF-8 -*-


import logging
import os

DEBUG = True

LOGGER_CONFIGURATION = {
    "LOGGER_NAME": "neko",
    "LOGGER_FORMAT": "[%(asctime)s] [%(levelname)s] %(message)s",
    "LOGGER_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",

    "ENABLE_CONSOLE_LOGGER": True,
    "CONSOLE_LOGGER_LEVEL": logging.DEBUG if DEBUG else logging.INFO,
    "CONSOLE_LOGGER_USE_COLORS": False,

    "ENABLE_FILE_LOGGER": True,
    "FILE_LOGGER_LEVEL": logging.DEBUG,
    "FILE_LOGGER_FILE_NAME": os.path.join(os.path.abspath(os.path.dirname(__file__)), "neko.log"),
    "FILE_LOGGER_FILE_MAX_SIZE": 2 * 1024 * 1024,
    "FILE_LOGGER_FILE_ENCODING": "UTF-8",
    "FILE_LOGGER_FILE_BACKUP_COUNT": 5
}
