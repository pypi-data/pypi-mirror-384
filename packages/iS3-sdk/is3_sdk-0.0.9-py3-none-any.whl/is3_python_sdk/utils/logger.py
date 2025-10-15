import logging
import os

from colorama import Fore, Style, init

# 初始化 colorama
init()


def Logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建自定义的日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 创建 FileHandler
    file_handler = logging.FileHandler(os.path.join(log_dir, 'info.log'), encoding='utf-8')
    file_handler.setFormatter(formatter)

    # 创建 StreamHandler
    stream_handler = logging.StreamHandler()

    # 设置日志级别
    stream_handler.setLevel(logging.DEBUG)  # 确保处理所有级别的日志

    # 定义不同级别的颜色
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            # 获取当前日志级别
            log_level = record.levelname
            # 设置颜色
            if log_level == 'INFO':
                color = Fore.WHITE
            elif log_level == 'ERROR':
                color = Fore.RED
            else:
                color = Fore.RESET
            # 设置日志消息格式
            log_message = super().format(record)
            # 返回带颜色的日志消息
            return f"{color}{log_message}{Style.RESET_ALL}"

    # 使用 ColoredFormatter
    colored_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(colored_formatter)

    # 配置日志记录器
    logging.basicConfig(
        level=logging.INFO,  # 确保处理所有级别的日志
        handlers=[file_handler, stream_handler]
    )
