from ..domain.data_dto import DataEntity
from .kafka_component_util import kafkaComponent

'''插件日志'''


def send_plugin_log(message, dataDto: DataEntity):
    pluginLog = {
        'message': message,
        'taskId': dataDto.taskId,
        'logId': dataDto.logId,
        'pluginCode': dataDto.serverName,
        'nodeId': dataDto.nodeId,
        'customInstanceCode': dataDto.customInstanceCode,
        'prjId': dataDto.prjId
    }
    topic = 'plugin-log-context'
    kafka_component = kafkaComponent(topic='plugin-log-context', group_id='DEFAULT_GROUP',
                                     bootstrap_servers=dataDto.bootstrapServers)
    kafka_component.send(topic, pluginLog)


'''任务日志（输入、执行结果、执行时间、输出）'''


def send_task_log(message, dataDto: DataEntity):
    taskLog = message
    taskLog['nodeId'] = dataDto.nodeId
    taskLog['taskId'] = dataDto.taskId
    taskLog['recordId'] = dataDto.taskInstanceId
    topic = 'task-log-context'
    kafka_component = kafkaComponent(topic=topic, group_id='DEFAULT_GROUP', bootstrap_servers=dataDto.bootstrapServers)
    kafka_component.send(topic, taskLog)
