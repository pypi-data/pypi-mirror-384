import logging
import time

def get_logger(name: str = "YouTubeCrawler", log_file: str = "app.log"):
    """
    Configures and returns a logger that logs to both the console and a file.

    Args:
        name (str): The name of the logger.
        log_file (str): The name of the file to save logs to.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Get a logger instance
    logger = logging.getLogger(name)
    
    # Set the lowest logging level to capture all messages
    logger.setLevel(logging.INFO)

    # This check prevents adding handlers multiple times if the function is called again
    if not logger.handlers:
        # Define the log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s : %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # --- Handler 1: Log to Console (StreamHandler) ---
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # --- Handler 2: Log to a File (FileHandler) ---
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def safe_sleep(seconds: float, logger):
    print(f"\rSleeping for {seconds} seconds to respect API rate limits...", end='', flush=True)
    time.sleep(seconds)

def keyword_loader(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        keywords = [line.strip() for line in file if line.strip() and line.startswith('#') is False]
    return keywords