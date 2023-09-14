import paho.mqtt.client as mqtt

#连接回调函数
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# 连接到MQTT代理
client = mqtt.Client()
client.on_connect = on_connect
client.connect("127.0.0.1", 1883)

# 发布消息到指定主题
topic = "m"
payload = "Hello, MQTT!"
qos_level = 1 #设置QoS等级
client.publish(topic, payload, qos_level) 

# 断开与MQTT代理的连接
client.disconnect()

