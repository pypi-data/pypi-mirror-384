import random
import socket
import threading

from ..config.load_config import get_config
from ..data_query.is3_python_api import iS3PythonApi

sequenceNum = 0
instanceId = random.randint(0, 2 ** 63 - 1)
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

config = get_config()
xAccessKey = config['key']['X-Access-Key']
xSecretKey = config['key']['X-Secret-Key']
headers = {
    'Content-Type': 'application/json',
    'X-Access-Key': xAccessKey,
    'X-Secret-Key': xSecretKey
}
iS3Addr = config['domain']['addr']


def time_task():
    global sequenceNum
    global instanceId
    global ip
    print("发送心跳")
    threading.Timer(10, time_task).start()
    requestId = random.randint(0, 2 ** 63 - 1)
    jsonData = {
        "requestId": requestId,
        "instanceId": instanceId,
        "sequenceNum": sequenceNum,
        "ip": ip,
    }
    is3Api = iS3PythonApi(headers, iS3Addr, None)
    response = is3Api.sendHeartbeat(jsonData)
    if response.get('code') == 500:
        sequenceNum = 0
        instanceId = random.randint(0, 2 ** 63 - 1)
    print(response)
    data = response.get('data')
    revRequestId = data.get('requestId')
    # 校验requestId是否相同
    if int(requestId) == int(revRequestId):
        sequenceNum = int(data.get("sequenceNum")) + 1
