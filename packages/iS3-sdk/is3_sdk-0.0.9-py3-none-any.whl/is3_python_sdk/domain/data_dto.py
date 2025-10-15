from typing import List


class DataEntity:
    def __init__(self, preData: List[int], pluginDataConfig: dict, taskInstanceId: int, taskId: int, nodeId: int,
                 logId: int, customInstanceCode: int, headers: str, serverName: str, prjId: int, tenantId: int, bootstrapServers: str):
        self.preData = preData
        self.pluginDataConfig = pluginDataConfig
        self.taskInstanceId = taskInstanceId
        self.taskId = taskId
        self.nodeId = nodeId
        self.logId = logId
        self.customInstanceCode = customInstanceCode
        self.headers = headers
        self.serverName = serverName
        self.prjId = prjId
        self.tenantId = tenantId
        self.bootstrapServers = bootstrapServers

        self.pre_node_data = preData.get('data', [])
        self.plugin_data_config = pluginDataConfig

    def __str__(self):
        return (f"DataEntity("
                f"preData={self.preData}, "
                f"pluginDataConfig='{self.pluginDataConfig}', "
                f"taskInstanceId={self.taskInstanceId}, "
                f"taskId={self.taskId}, "
                f"nodeId={self.nodeId}, "
                f"logId={self.logId}, "
                f"customInstanceCode={self.customInstanceCode}, "
                f"headers='{self.headers}', "
                f"serverName='{self.serverName}', "
                f"prjId={self.prjId}, "
                f"tenantId={self.tenantId}, "
                f"bootstrapServers='{self.bootstrapServers}')"
                )
