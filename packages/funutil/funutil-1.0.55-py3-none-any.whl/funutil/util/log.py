import os
import sys
from functools import cache

from loguru import logger

if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)
    with open("logs/.gitignore", "w") as f:
        f.write("*")

logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} |<lvl>{level:8}</>| {name} : {module}:{line:4} | <cyan>{extra[module_name]}</> | - <lvl>{message}</>",
            "colorize": True,
            "level": "INFO",
        },
        {
            "sink": "logs/all.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} |{level:8}| {name} : {module}:{line:4} | {extra[module_name]} | - {message}",
            "colorize": False,
            "rotation": "00:00",
            "compression": "gz",
            "retention": 30,
            "level": "INFO",
        },
    ]
)


@cache
def get_logger(name="default", level="INFO", formatter=None, *args, **kwargs):
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
        with open("logs/.gitignore", "w") as f:
            f.write("*")
    logger.add(
        sink=f"logs/{name}.log",
        format=formatter
        or "{time:YYYY-MM-DD HH:mm:ss.SSS} |{level:8}| {name} : {module}:{line:4} | {extra[module_name]} | - {message}",
        filter=lambda record: record["extra"].get("module_name") == name,
        level=level,
        rotation="00:00",
        compression="gz",
        retention=7,
        colorize=False,
    )
    return logger.bind(module_name=name)


def getLogger(
    name="default", level="INFO", formatter=None, handler=None, *args, **kwargs
):
    return get_logger(name, level=level, formatter=formatter, handler=handler)
