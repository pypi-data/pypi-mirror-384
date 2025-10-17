import os
import sys
import logging
from datetime import datetime

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass  # No-op for compatibility


def setup_logger(file_name_suffix: str = 'logger', path_logger: str = os.getcwd()):
    """
    Set up a logger that writes messages both to the console (stdout)
    and to a timestamped log file.

    Parameters
    ----------
    file_name_suffix : str, optional
        A custom suffix for the log file name (default: 'logger').
        The final file name will be of the form:
        '<file_name_suffix>_YYYY-MM-DD_HH-MM-SS.txt'.

    path_logger : str, optional
        Directory path where the log file will be stored
        (default: current working directory).

    Returns
    -------
    logger : logging.Logger
        Configured logger instance that writes to both console and
        the generated log file.
    """

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join(path_logger, f"{file_name_suffix}_{timestamp}.txt")

    logger = logging.getLogger("RedirectedOutput")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler (timestamped name)
    file_handler = logging.FileHandler(logfile, mode="w")
    file_handler.setFormatter(formatter)

    # Console handler (real-time stdout)
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
