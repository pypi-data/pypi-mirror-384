import logging

from .file_logger import file_logging_handler
from .stash_logger import stash_logging_handler


def init_logging(app, logger_name: str, logger_type: str = "file"):
    if logger_type == "file":
        handler = file_logging_handler(app)
    else:
        handler = stash_logging_handler(app)

    root_logger = logging.getLogger(logger_name)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    # 如果开启 DEBUG，则同步输出到控制台
    if app.config.get("DEBUG", False):
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        console.setFormatter(formatter)
        root_logger.addHandler(console)
