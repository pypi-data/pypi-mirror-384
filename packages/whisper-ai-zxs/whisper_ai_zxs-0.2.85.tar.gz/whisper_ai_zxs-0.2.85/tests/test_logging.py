from whisper_ai_zxs.logging_config import setup_logging
import logging

logger = logging.getLogger("whisper_ai")

def test_logging():
    logger.debug("测试：debug")
    logger.info("测试：info")
    logger.warning("测试：warning")
    logger.error("测试：error")
    logger.critical("测试：critical")
