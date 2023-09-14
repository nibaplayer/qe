import json
import time

import paho.mqtt.client as mqtt

from multiprocessing import Process,Queue
from threading import Thread


def on_message_op(client, userdata, message):
    #这里添加dingding机器人
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

broker_address = "10.214.131.229"
port = 1883
client = mqtt.Client("Sublisher")
client.connect(broker_address, port)
# 设置消息接收回调函数

data={
    "id": "container-value-cam1-mechanical-1-interval",
    "name": "mts",
    "score": 16.0,
    "status": True
}
def sub():
    client.subscribe("m")
    client.on_message = on_message_op
    client.loop_forever()
th=Thread(target=sub)
th.start()
client_pub = mqtt.Client("Publisher")
client_pub.connect(broker_address, port)
client_pub.publish("topic/mts",payload=json.dumps(data))
time.sleep(3)
client_pub.disconnect()
client.disconnect()