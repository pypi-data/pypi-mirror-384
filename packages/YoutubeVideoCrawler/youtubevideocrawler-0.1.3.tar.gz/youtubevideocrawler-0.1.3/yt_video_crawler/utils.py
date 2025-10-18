import logging
import time
import sys

class FlexibleLogger(logging.Logger):
    def __init__(self, name, log_file="app.log"):
        super().__init__(name, logging.INFO)
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s : %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.log_file = log_file

    def _log_to_console(self, message, level):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self.formatter)
        self.addHandler(handler)
        self.log(level, message)
        self.removeHandler(handler)

    def _log_to_file(self, message, level):
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(self.formatter)
        self.addHandler(handler)
        self.log(level, message)
        self.removeHandler(handler)

    def _log_with_dest(self, level, message, print_to="both"):
        if print_to in ("console", "both"):
            self._log_to_console(message, level)
        if print_to in ("file", "both"):
            self._log_to_file(message, level)

    def debug(self, message, print_to="both"):
        self._log_with_dest(logging.DEBUG, message, print_to)

    def info(self, message, print_to="both"):
        self._log_with_dest(logging.INFO, message, print_to)

    def warning(self, message, print_to="both"):
        self._log_with_dest(logging.WARNING, message, print_to)

    def error(self, message, print_to="both"):
        self._log_with_dest(logging.ERROR, message, print_to)

    def critical(self, message, print_to="both"):
        self._log_with_dest(logging.CRITICAL, message, print_to)


def get_logger(name="YouTubeCrawler", log_file="app.log"):
    """Create and return a FlexibleLogger instance."""
    logging.setLoggerClass(FlexibleLogger)
    return FlexibleLogger(name, log_file)


def safe_sleep(seconds: float, logger = None):
    # print(f"\rSleeping for {seconds} seconds to respect API rate limits...", end='', flush=True)
    if logger:
        logger.info(f"Sleeping for {seconds} seconds...")
    time.sleep(seconds)

def keyword_loader(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        keywords = [line.strip() for line in file if line.strip() and line.startswith('#') is False]
    return keywords