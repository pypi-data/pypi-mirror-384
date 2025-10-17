import sys
import os
import logging
from datetime import datetime


class Logger:
    EXCEPTION = 100
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self):
        today = datetime.strftime(datetime.now(), "%d-%m-%y-%H_%M_%S")

        os.makedirs("logs", exist_ok=True)
        log_path = f"logs/log-{today}.log"

        # 🔹 Set default logging config (your requested format)
        logging.basicConfig(
            level=logging.INFO,
            format=u'%(filename)s:%(funcName)s:%(lineno)d '
                   '#%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
            datefmt="%d/%b/%y %H:%M:%S",
        )

        logger_name = "YoYoLogger"
        self.__log = logging.getLogger(logger_name)

        # Avoid re-adding handlers
        if not self.__log.handlers:
            # 🔹 Console handler
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                u'%(filename)s:%(funcName)s:%(lineno)d '
                '#%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
                datefmt="%d/%b/%y %H:%M:%S"
            ))

            # 🔹 File handler
            file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                u'%(filename)s:%(funcName)s:%(lineno)d '
                '#%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
                datefmt="%d/%b/%y %H:%M:%S"
            ))

            # Attach both
            self.__log.addHandler(console_handler)
            self.__log.addHandler(file_handler)

        self.__log.setLevel(self.INFO)

        # Map levels to functions
        self.__methods_map = {
            self.DEBUG: self.__log.debug,
            self.INFO: self.__log.info,
            self.WARNING: self.__log.warning,
            self.ERROR: self.__log.error,
            self.CRITICAL: self.__log.critical,
            self.EXCEPTION: self.__log.exception,
        }

    def __call__(self, lvl, msg, *args, **kwargs):
        """Log with the given level."""
        if lvl in self.__methods_map:
            self.__methods_map[lvl](msg, *args, **kwargs)
        else:
            self.__log.log(lvl, msg, *args, **kwargs)

    def set_level(self, level=None):
        if level is None:
            level = self.INFO
        self.__log.setLevel(level)
