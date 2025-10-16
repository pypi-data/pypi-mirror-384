import logging

def setup_logger(logger_name: str = "logger", log_file: str = None):
    # Get or create the logger
    logger = logging.getLogger(logger_name)
    
    # Prevent adding duplicate handlers by removing existing handlers first
    logger.handlers.clear()
    
    # Reset the logger's propagation and level
    logger.propagate = False
    logger.setLevel(logging.INFO)

    # StreamHandler for logging to console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)

    # Optionally, log to a file
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger, stream_handler