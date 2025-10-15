"""Top-level package for T - Page Object."""

import logging
import sys

from t_page_object.bot_config import BotConfig

log_format = logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s")
log_level = logging.DEBUG if BotConfig.enable_logging else logging.INFO

logger = logging.getLogger("t_page_object")
if logger.hasHandlers():
    logger.handlers = []
logger.setLevel(log_level)
logger.propagate = False

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level)
handler.setFormatter(log_format)
logger.addHandler(handler)

__author__ = """Thoughtful"""
__email__ = "support@thoughtful.ai"
__version__ = "__version__ = '1.1.5'"
