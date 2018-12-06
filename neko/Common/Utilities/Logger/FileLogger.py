# -*- encoding: UTF-8 -*-


import logging.handlers


class FileLogger(logging.handlers.RotatingFileHandler):
    def __init__(self, file_name, file_max_size, file_encoding, file_backup_count):
        super().__init__(
            filename = file_name,
            maxBytes = file_max_size,
            encoding = file_encoding,
            backupCount = file_backup_count
        )
