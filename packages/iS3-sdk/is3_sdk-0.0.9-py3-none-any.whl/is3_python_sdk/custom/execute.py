from abc import ABC, abstractmethod

from ..config.config_model import ConfigModel
from ..domain.data_dto import DataEntity


# 定义抽象基类
class Execute(ABC):
    def __init__(self, config_json):
        config_model = ConfigModel(config_json)
        from .iS3PythonCore import iS3PythonCore
        self.iS3_python_core = iS3PythonCore(config_model)

    def start(self):
        self.iS3_python_core.startPlugin(self)

    def send_plugin_log(self, message, dataDto: DataEntity):
        self.iS3_python_core.send_plugin_log(message=message, dataDto=dataDto)

    @abstractmethod
    def execute_custom(self, dataDto: DataEntity):
        pass
