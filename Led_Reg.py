import base64
from collections import OrderedDict
import time
import pickle
import base64
import zlib
import redis
import paho.mqtt.client as mqtt
import json


def pack(v):
    return zlib.compress(base64.b64encode(pickle.dumps(v)))

def unpack(v):
    return pickle.loads(base64.b64decode(zlib.decompress(v)))

class Redis:
    def __init__(self, IP, port):
        self.IP = IP
        self.port = port
        self.pool = redis.ConnectionPool(host=IP, port=port)

    def getPipe(self):
        r = redis.Redis(connection_pool=self.pool)
        return r.pipeline()

    def getR(self):
        return redis.Redis(connection_pool=self.pool)

    def save_a_dict(self, dd):
        if not isinstance(dd, dict):
            return
        pipe = self.getPipe()
        for k, v in dd.items():
            if self.getR().exists(k):
                pipe.delete(k)
            if not isinstance(v, dict) or v == {}:
                continue
            for k1, v1 in v.items():
                if not isinstance(k1, str):
                    continue
                pipe.hset(k, k1, pack(v1))
            pipe.set(k + "_dict", pack(v))
        pipe.execute()
        pipe.close()

    def get_a_dict(self, hashName):
        r = redis.Redis(connection_pool=self.pool)
        d = r.get(hashName + "_dict")
        if d == None:
            return None
        r.close()
        return unpack(d)

    def close(self):
        self.pool.disconnect()

    def __del__(self):
        try:
            self.pool.disconnect()
        except Exception:
            pass



client=Redis(IP="10.214.131.229",port=6379)


from PIL import Image
from io import BytesIO
import base64
def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
def get_rgb_brightness_from_base64(base64_str,th=150):
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    image = image.convert("RGB")

    width, height = image.size
    pixels = width * height

    r_sum = g_sum = b_sum = 0

    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            r_sum += r
            g_sum += g
            b_sum += b

    r_brightness = r_sum / pixels
    g_brightness = g_sum / pixels
    b_brightness = b_sum / pixels
    if r_brightness > g_brightness and r_brightness > b_brightness:
        color = "Red"
        if r_brightness>th:
            power="on"
        else:
            power="off"
    elif g_brightness > r_brightness and g_brightness > b_brightness:
        color = "Green"
        if g_brightness > th:
            power = "on"
        else:
            power = "off"
    else:
        color = "Blue"
        if b_brightness > th:
            power = "on"
        else:
            power = "off"

    return power,color


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
    

broker_address = "10.214.131.229"
port = 1883


while(True):
    try:
        ids=unpack(client.getR().get("Monitor_Containers_Id"))
        for id in ids:
            Rpipe = client.getPipe()
            if "LED" in id:
                image=client.getR().hget("Camera_Monitor_SubImage",id)
                if image!=None:
                    image=unpack(image)
                    p,c=get_rgb_brightness_from_base64(image)
                    Rpipe.hset(f"Monitor_{id}", "value",f"{c}_{p}")
                    Rpipe.hset(f"Monitor_{id}", "timestamp", getTimeStampStr())
                    print(f"Monitor_{id}",c,p)
                    id = id.replace("-","_")
                    data={
                        "id": id,
                        "name": f"{c}_{p}",
                        "score": float(0),
                        "status": True
                    }
                    send2mqtt(id, data, broker_address, port)
                    #print(id, data, broker_address, port)
            Rpipe.execute()
    except:
        pass
    time.sleep(10)