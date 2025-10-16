import logging

logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("azure").setLevel(logging.CRITICAL)


def get_logger(name: str = "curcuma", level: int = logging.INFO):
    logger = logging.getLogger(name)
    LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s"

    try:
        import coloredlogs

        coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT)
    except ModuleNotFoundError:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger
