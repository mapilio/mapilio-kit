import logging
from logging.handlers import RotatingFileHandler


class MapilioLogger:
    def __init__(self, name=None, log_file=None, level=logging.DEBUG):
        if name is None:
            name = __name__
        self.logger = logging.getLogger(name)

        if not self.logger.hasHandlers():
            self.logger.setLevel(level)

            log_format = logging.Formatter('%(levelname)s - %(message)s')

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            self.logger.addHandler(console_handler)

            if log_file:
                file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2)  # 5MB per file
                file_handler.setFormatter(log_format)
                self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger