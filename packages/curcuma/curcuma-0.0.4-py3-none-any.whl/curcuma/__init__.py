import os

# import sys
# from loguru import logger

from .client import Client, AzureClient, CloudClient
from .exceptions import *

package_name = os.path.basename(os.path.dirname(__file__))
# logger.disable(package_name)

# def configure_logger(log_level: str = "INFO"):
#     logger.enable(package_name)
#     logger.remove()
#     logger.add(
#         sys.stdout,
#         format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}",
#         level=log_level.upper(),
#     )
