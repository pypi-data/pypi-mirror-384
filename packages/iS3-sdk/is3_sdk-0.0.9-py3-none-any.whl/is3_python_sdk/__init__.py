__version__ = "1.2.7"

# 导出主要 API 类（避免循环导入）
from .data_query.is3_python_api import iS3PythonApi
from .config.config_model import ConfigModel

# 导出数据实体
from .domain.data_dto import DataEntity
from .domain.task_data import TaskDataDef

# 导出工具类
from .utils.logger import Logging
from .utils.fileUtil import FileUtil
from .utils.is3_request_util import RequestUtil

__all__ = [
    'iS3PythonApi',
    'ConfigModel', 
    'DataEntity',
    'TaskDataDef',
    'Logging',
    'FileUtil',
    'RequestUtil'
]
