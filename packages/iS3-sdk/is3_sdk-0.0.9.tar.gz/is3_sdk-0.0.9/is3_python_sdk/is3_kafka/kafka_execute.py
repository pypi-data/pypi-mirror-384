import json
from datetime import datetime

from ..custom.execute import Execute
from ..domain.data_dto import DataEntity
from ..utils.kafka_component_util import kafkaComponent
from ..utils.log_util import send_task_log
from ..utils.logger import Logging

status = ""

Logging()


class KafkaProcessor:

    def __init__(self, serverName, headers, bootstrap_servers):
        self.serverName = serverName
        self.headers = headers
        self.group_id = 'data-central-group'
        self.bootstrap_servers = bootstrap_servers
        self.kafka_component = kafkaComponent(topic=serverName, group_id=self.group_id,
                                              bootstrap_servers=self.bootstrap_servers)

    def processor(self, execute: Execute):
        err = ""
        global status
        topic = 'task-distribute-center'
        kafka_consumer = self.kafka_component
        while True:
            start_time = datetime.now()
            data = kafka_consumer.receive()
            try:
                dataDto = DataEntity(preData=data.get('data', []),
                                     pluginDataConfig=json.loads(data.get('pluginDataConfig', {})),
                                     taskInstanceId=data.get('taskInstanceId', 0), taskId=data.get('taskId', 0),
                                     nodeId=data.get('nodeId', 0),
                                     logId=data.get('logId', 0), headers=self.headers, serverName=self.serverName,
                                     prjId=data.get('prjId', 0),
                                     customInstanceCode=data.get('customInstanceCode', ''),
                                     tenantId=data.get('tenantId', 0), bootstrapServers=self.bootstrap_servers)
                custom = execute
                result = custom.execute_custom(dataDto)
                message = {'data': result, 'taskId': dataDto.taskId, 'logId': dataDto.logId, 'nodeId': dataDto.nodeId,
                           'prjId': dataDto.prjId, 'taskInstanceId': dataDto.taskInstanceId,
                           'tenantId': data.get('tenantId', '')}
                self.kafka_component.send(topic, message)
                status = "执行成功"
            except Exception as e:
                err = f"发生异常: {e}"
                continue
            end_time = datetime.now()
            upSecond = (end_time - start_time).total_seconds()
            message_1 = {'importData': data, 'upSecond': upSecond, 'outputData': result, 'statuDesc': status,
                         'exceptionInfo': err}
            send_task_log(message_1, dataDto)
