from ..config import config_model
from .execute import Execute
from ..data_query.is3_python_api import iS3PythonApi
from ..domain.data_dto import DataEntity
from ..is3_kafka.kafka_execute import KafkaProcessor
from ..utils.kafka_component_util import kafkaComponent


class iS3PythonCore:
    def __init__(self, config: config_model):
        self.config = config

    def startPlugin(self, execute: Execute):
        processor = KafkaProcessor(self.config.uniquePluginCode, self.config.headers, self.config.kafkaUrl)
        processor.processor(execute)

    def send_plugin_log(self, message, dataDto: DataEntity):
        pluginLog = {
            'message': message,
            'taskId': dataDto.taskId,
            'logId': dataDto.logId,
            'pluginCode': self.config.uniquePluginCode,
            'nodeId': dataDto.nodeId,
            'customInstanceCode': dataDto.customInstanceCode,
            'prjId': dataDto.prjId
        }
        topic = 'plugin-log-context'
        kafka_component = kafkaComponent(topic='plugin-log-context', group_id='DEFAULT_GROUP',
                                         bootstrap_servers=self.config.kafkaUrl)
        kafka_component.send(topic, pluginLog)

    def createAPIClient(self, dataDto: DataEntity):
        return iS3PythonApi(headers=self.config.headers, iS3Addr=self.config.serverUrl, prjId=dataDto.prjId,
                            dataDto=dataDto)

    def create_data_entity(self, plugin_data_config, pre_node_data):
        # 输入数据
        dataDto = DataEntity(
            preData={"data": pre_node_data},
            pluginDataConfig=plugin_data_config,
            taskInstanceId=1111,
            taskId=1,
            nodeId=1,
            customInstanceCode=1,
            logId=1,
            serverName=self.config.uniquePluginCode,
            headers=self.config.headers,
            prjId=self.config.prjId,
            tenantId=1,
            bootstrapServers=self.config.kafkaUrl,
        )
        return dataDto
