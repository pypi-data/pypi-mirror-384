from abc import ABC, abstractmethod

from ..config.config_model import ConfigModel
from .iS3PythonCore import iS3PythonCore


# 定义抽象基类
class test_data_base(ABC):
    def __init__(self, configJSON):
        self.config_model = ConfigModel(configJSON)
        self.iS3_python_core = iS3PythonCore(self.config_model)

    def start(self):
        try:
            self.iS3_python_core.startPlugin()
        except Exception as e:
            raise RuntimeError(f"Failed to start plugin: {str(e)}")

    @abstractmethod
    def generate_test_data(self):
        pass

    @abstractmethod
    def generate_test_config(self):
        pass

    def generate_test_dto(self):
        try:
            pre_node_data = self.generate_test_data()
            plugin_data_config = self.generate_test_config()
            return self.iS3_python_core.create_data_entity(plugin_data_config=plugin_data_config,
                                                           pre_node_data=pre_node_data)

        except Exception as e:
            raise RuntimeError(f"Failed to generate test DTO: {str(e)}")

    def generate_test_taskJson(self):
        try:
            data = self.generate_test_data()
            return {
                "customCode": self.config_model.taskFlowCode,
                "data": data
            }
        except Exception as e:
            raise RuntimeError(f"Failed to generate test task JSON: {str(e)}")
