from logging.config import dictConfig

from storeapi.config import DevConfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {  # from the same request
                    "()": "asgi_correlation_id.CorrelationIdFilter",  # after the parenthesis, any keyword pair arguments
                    # filter = asgi_correlation_id.CorrelationIdFilter(uuid_length=8, default_value="-")
                    "uuid_length": 8
                    if isinstance(config, DevConfig)
                    else 32,  # uuid universally unique identifier
                    "default_value": "-",  # not in a request
                }
            },
            "formatters": {
                "console": {
                    # "class": "logging.Formatter",  # we don't need it because we use rich
                    # "datefmt": "%Y-%m-%dT%H:%M:%S", # we don't need it because we use rich
                    "format": "(%(correlation_id)s)(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",  # "class": "logging.Formatter"   this not json
                    # the format doesn't care if it's json, it would just pick the variables to create the json
                    # "format": "%(asctime)s %(msecs)03dZ | %(levelname)-8s | %(correlation_id)s %(name)s %(lineno)d - %(message)s",  # noqa: E501  03dz 3 digits ISO  format
                    "format": "%(asctime)s %(msecs)03dZ %(levelname)-8s %(correlation_id)s %(name)s %(lineno)d %(message)s",  # noqa: E501
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id"],
                },
                "rotating_file": {  # to be used for example with logs from uvicorn and storeapi
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024 * 1,  # 1MB
                    "backupCount": 2,  # it only keeps 2 backups in total, so 2 * 1 = 2MB of logs
                    "encoding": "utf8",  # English
                    "filters": ["correlation_id"],
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default", "rotating_file"],
                    "level": "INFO",
                },  # logs comming from uvicorn with the same format
                "storeapi": {  # root.storeapi.routers.post
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,  # not to propagate to the root
                },
                "databases": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },  # logs comming from databases with the same format
                "aiosqlite": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },  # logs comming from aiosqlite with the same format
                "fastapi": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },
            },
        }
    )
