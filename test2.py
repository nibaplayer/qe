import paho.mqtt.client as mqtt
import json
import redis
from db_server import util
# 设置MQTT代理的地址和端口
broker_address = "10.214.131.229"
broker_port = 1883

# 创建MQTT客户端
client = mqtt.Client()

# 连接到MQTT代理
client.connect(broker_address, broker_port)


r = redis.Redis(host='10.214.131.229', port=6379)
hash_name = "monitor_profile"
fields = r.hkeys(hash_name) #读取所有fields 提取阈值
#创建哈希表用于存储阈值
# intervals = {}
for field in fields:
   temp = field.decode()
   if "interval" in temp and "digital" in temp:
    #   temp_intervals = util.unpack(r.hget(hash_name,temp))
    #   temp_intervals = temp_intervals.strip("()")
    #   temp_intervals = temp_intervals.replace("inf","100000000") #把默认的inf替换掉
      
        temp = temp.replace("-interval","")
        temp = temp.replace("-","_")
        print(temp)
    #   intervals[temp] = temp_intervals.split(",") #字典中的temp为修改后的   -全部替换为_
      #每张表要创建一条流
        # topic = temp
        # data={
        #     "id": temp,
        #     "name": "mts",
        #     "score": float(20),
        #     "status": True 
        # }
        # client.publish(topic, payload=json.dumps(data))

        # # 断开与MQTT代理的连接
        # client.loop_start()  # 开始循环，确保消息发送成功
        # client.loop_stop()  # 停止循环后断开连接


# 发布消息