import json
import time

import paho.mqtt.client as mqtt

from multiprocessing import Process,Queue
from threading import Thread
from dingtalkchatbot.chatbot import DingtalkChatbot, ActionCard, CardItem

#这里添加dingding机器人
#连接机器人
# WebHook地址
webhook = 'https://oapi.dingtalk.com/robot/send?access_token=392f7b54e47dc479419a780bc4f0a71c7fcd0a3d36c34705bbdfbd5c2acb4cea'
secret = 'SECdbd565f7107144b0717daed4cbf4bdbd36d0b6e1e3cae998423e50e109ea74dc'  # 可选：创建机器人勾选“加签”选项时使用
xiaoding = DingtalkChatbot(webhook, secret=secret)  # 方式二：勾选“加签”选项时使用（v1.5以上新功能）

def on_message_op(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")
    xiaoding.send_text(message.payload.decode(), is_at_all=False)  #当前读数超过阈值后会一直报警
    


broker_address = "10.214.131.229"
port = 1883
client = mqtt.Client("Sublisher")
client.connect(broker_address, port)
# 设置消息接收回调函数



client.subscribe("m")
client.on_message = on_message_op
client.loop_forever()

# time.sleep(3)
# client.disconnect()