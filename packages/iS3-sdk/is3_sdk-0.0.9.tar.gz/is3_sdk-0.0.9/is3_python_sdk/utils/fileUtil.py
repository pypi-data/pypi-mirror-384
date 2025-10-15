import json
import logging
import os
import random
import shutil
from datetime import datetime

import requests

from .logger import Logging

Logging()


class FileUtil:

    @staticmethod
    def basePath():
        # 获取当前工作目录
        return os.getcwd()

    @staticmethod
    def generateTempDir():
        # 获取格式化的当前时间
        date_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # 生成随机数
        random_num = random.randint(1000, 9999)

        return f"{date_str}_{random_num}"

    @staticmethod
    def copyFile(source_url: str, dest_path: str):
        try:
            if os.path.isfile(source_url):
                shutil.copy(source_url, dest_path)
                logging.info(f"复制文件:\n源路径: {source_url}\n目标路径: {dest_path}")
            else:
                logging.error(f"源路径 not found: {source_url}")
                raise FileNotFoundError(f"源路径 not found: {source_url}")
        except Exception as e:
            logging.error(f"文件复制错误: {e}")
            raise

    @staticmethod
    def downloadFile(url: str, dest_path: str):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(dest_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"下载文件:\nURL: {url}\n保存路径: {dest_path}")
        except Exception as e:
            logging.error(f"文件下载错误: {e}")
            raise


