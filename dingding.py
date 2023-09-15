from dingtalkchatbot.chatbot import DingtalkChatbot, ActionCard, CardItem
import paho.mqtt.client as mqtt


#连接机器人
# WebHook地址
webhook = 'https://oapi.dingtalk.com/robot/send?access_token=392f7b54e47dc479419a780bc4f0a71c7fcd0a3d36c34705bbdfbd5c2acb4cea'
secret = 'SECdbd565f7107144b0717daed4cbf4bdbd36d0b6e1e3cae998423e50e109ea74dc'  # 可选：创建机器人勾选“加签”选项时使用
# 初始化机器人小丁
# xiaoding = DingtalkChatbot(webhook)  # 方式一：通常初始化方式
xiaoding = DingtalkChatbot(webhook, secret=secret)  # 方式二：勾选“加签”选项时使用（v1.5以上新功能）
# xiaoding = DingtalkChatbot(webhook, pc_slide=True)  # 方式三：设置消息链接在PC端侧边栏打开（v1.5以上新功能）

# # Text消息@所有人   这放在mqtt的on_message中
# xiaoding.send_text(msg='test', is_at_all=True)

#订阅mqtt
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # 订阅主题
    topic = "m"
    qos_level = 1 #设置QoS等级  因为一直报警的关系 这里其实关系不大
    client.subscribe(topic, qos_level)

def on_message(client, userdata, msg):
    #添加判断 
    #阈值需要每次去读 <<<<-----------
    print("Received message: "+msg.payload.decode())
    xiaoding.send_text(msg.payload.decode(), is_at_all=False)  #当前读数超过阈值后会一直报警


# 创建MQTT客户端
client = mqtt.Client()  

# 设置连接回调函数
client.on_connect = on_connect

# 设置消息接收回调函数
client.on_message = on_message

# 连接到MQTT代理
client.connect("127.0.0.1", 1883)  # 替换为你的MQTT代理地址和端口

# 保持连接
client.loop_forever()