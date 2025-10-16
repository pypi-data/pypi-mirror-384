import logging

# Create a logger object.
logger = logging.getLogger("myApp")

# logger.setLevel(logging.INFO)
logging.addLevelName(25, "NOTICE")
logging.addLevelName(35, "SUCCESS")


def notice(self, message, *args, **kwargs):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kwargs)


def success(self, message, *args, **kwargs):
    if self.isEnabledFor(35):
        self._log(35, message, args, **kwargs)


logging.Logger.success = success
logging.Logger.notice = notice

LOG_FORMAT = "%(asctime)s.%(msecs)03d [%(name)s] %(levelname)-8s %(message)s"

try:
    import coloredlogs

    coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT)
except ModuleNotFoundError:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)

logger.setLevel(logging.DEBUG)

logger.debug("this is a debugging message")
logger.info("this is an informational message")
logger.notice("this is a notice message")
logger.warning("this is a warning message")
logger.success("this is a success message")
logger.error("this is an error message")
logger.critical("this is a critical message")
