import json

from ..domain.data_dto import DataEntity


def create_data_entity(config, jsonData):
    serverName = config.get('server', 'plugin-code')
    xAccessKey = config['key']['X-Access-Key']
    xSecretKey = config['key']['X-Secret-Key']
    headers = {
        'Content-Type': 'application/json',
        'X-Access-Key': xAccessKey,
        'X-Secret-Key': xSecretKey
    }
    bootstrapServers = config['kafka']['bootstrap-servers']
    dataDto = DataEntity(
        preData=jsonData.get('data', {}),
        pluginDataConfig=jsonData.get('pluginDataConfig', {}),
        taskInstanceId=1111,
        taskId=1,
        nodeId=1,
        customInstanceCode=1,
        logId=1,
        serverName=serverName,
        headers=headers,
        prjId=int(json.dumps(jsonData.get('prjId', 1))),
        tenantId=1,
        bootstrapServers=bootstrapServers,
    )
    return dataDto
