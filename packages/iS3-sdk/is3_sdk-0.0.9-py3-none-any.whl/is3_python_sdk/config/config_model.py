class ConfigModel:
    def __init__(self, configJSON):
        self.serverUrl = ""
        self.kafkaUrl = ""
        self.prjId = 0
        self.xAccessKey = ""
        self.xSecretKey = ""
        self.pluginCode = ""
        self.pluginVersion = None
        self.taskFlowCode = ""
        self.callbackWebSocketUrl = ""
        self.callbackTopic = ""
        try:
            if "server" in configJSON:
                self.serverUrl = configJSON["server"].get("serverUrl", "")
            self.kafkaUrl = configJSON["server"].get("kafkaUrl", "")
            if "key" in configJSON:
                self.prjId = configJSON.get("key", {}).get("prjId", 0)
                self.xAccessKey = configJSON["key"].get("xAccessKey", "")
                self.xSecretKey = configJSON["key"].get("xSecretKey", "")
            if "plugin" in configJSON:
                self.pluginCode = configJSON["plugin"].get("pluginCode", "")
                self.pluginVersion = configJSON["plugin"].get("pluginVersion", "")
            if "task" in configJSON:
                self.taskFlowCode = configJSON["task"].get("taskFlowCode", "")
            if "callback" in configJSON:
                self.callbackWebSocketUrl = configJSON["callback"].get("websocketUrl", "")
                self.callbackTopic = configJSON["callback"].get("topic", "")
        except KeyError as e:
            raise KeyError(f"Missing required configuration key: {e}")

        if self.pluginVersion:
            self.uniquePluginCode = self.pluginCode + "-" + self.pluginVersion.replace(".", "-")
        else:
            self.uniquePluginCode = self.pluginCode

        self.headers = {
            'Content-Type': 'application/json',
            'X-Access-Key': self.xAccessKey,
            'X-Secret-Key': self.xSecretKey
        }
