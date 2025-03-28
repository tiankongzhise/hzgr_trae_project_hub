import logging
import sys

# 创建根日志器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

# 添加处理器到日志器
logger.addHandler(console_handler)

def get_logger(name=None):
    """获取日志器"""
    return logging.getLogger(name) if name else logger