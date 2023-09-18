import paho.mqtt.client as mqtt
import json 

#连接回调函数
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def send2mqtt(topic, data, add, port):
#     print("sended")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(add, port)
    print(topic,add,port)

    client.publish(topic, payload=json.dumps(data))
#     client.publish(topic, "1")
    
    client.loop_start()  # 开始循环，确保消息发送成功
    client.loop_stop()  # 停止循环后断开连接

add="10.214.131.229"
port=1883
topic = "container_value_cam1_LED_7"

data={
    "id": "container_value_cam1_LED_7",
    "name": "on",
    "score": float(0),
    "status": True
}
send2mqtt(topic,data,add,port)

