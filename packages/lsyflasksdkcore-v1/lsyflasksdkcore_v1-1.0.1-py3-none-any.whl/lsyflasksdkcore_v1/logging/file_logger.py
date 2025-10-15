import logging
from logging.handlers import TimedRotatingFileHandler


def file_logging_handler(app):
    f_handler = TimedRotatingFileHandler(
        filename="hasami",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        delay=True,  # only open file on first emit, avoids lock-on-rollover
    )

    # 优化后的日志格式（包含具体代码路径）
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    out_fmt = "[{asctime}] [{levelname:<6}] {pathname}:{lineno} - {funcName}(): {message}"  # 修改点
    logger_fmt = logging.Formatter(out_fmt, dt_fmt, style="{")
    f_handler.setFormatter(logger_fmt)

    f_handler.suffix = "%Y-%m-%d.log"
    return f_handler


"""
import logging
from logging.handlers import TimedRotatingFileHandler


class LevelFilter:
    # 日志级别过滤器

    def __init__(self, level):
        self._level = level

    def filter(self, record):
        return record.levelno == self._level


def file_logging_handler(app):
    # 配置INFO级别日志处理器
    info_handler = TimedRotatingFileHandler(
        filename="hasami_info.log",  # INFO日志文件名
        when='midnight',
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(LevelFilter(logging.INFO))  # 只处理INFO级别

    warning_handler = TimedRotatingFileHandler(
        filename="hasami_warning.log",
        when='midnight',
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(LevelFilter(logging.WARNING))

    # 配置ERROR级别日志处理器
    error_handler = TimedRotatingFileHandler(
        filename="hasami_error.log",  # ERROR日志文件名
        when='midnight',
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(LevelFilter(logging.ERROR))  # 只处理ERROR及以上

    # 通用日志格式配置
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    out_fmt = "[{asctime}] [{levelname:<6}] {pathname}:{lineno} - {funcName}(): {message}"
    formatter = logging.Formatter(out_fmt, dt_fmt, style="{")

    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # 获取根日志记录器并添加处理器
    logger = logging.getLogger()
    logger.addHandler(info_handler)
    logger.addHandler(warning_handler)
    logger.addHandler(error_handler)

    # 返回处理器对象（可选）
    return info_handler, warning_handler, error_handler
"""
