import logging
from colorlog import ColoredFormatter

def get_logger(name : str, level : int) -> logging.Logger:
    """returns a Logger instance for a file

    Args:
        name (str): Name of the logger
        level (int): Debug level 
                    (0 -> Error, 1 -> Info, other -> Debug)

    Returns:
        logging.Logger: Logger Object
    """
    l = logging.getLogger(name)

    if level == 0:
        l.setLevel(logging.ERROR)
    if level == 1:
        l.setLevel(logging.INFO)
    else:
        l.setLevel(logging.DEBUG)

    stream_h = logging.StreamHandler()
    file_h = logging.FileHandler('logs/%s.log' % name)

    formatter = ColoredFormatter(
        "%(asctime)-s %(name)s [%(levelname)s] %(log_color)s%(message)s%(reset)s",
        datefmt=None, reset=True,
        log_colors={
            "DEBUG": "purple",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        }
    )

    stream_h.setFormatter(formatter)
    file_h.setFormatter(formatter)
    l.addHandler(stream_h)
    l.addHandler(file_h)

    return l