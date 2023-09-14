import base64
from collections import OrderedDict
import time
import pickle
import base64
import zlib
import redis
import io
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib import pyplot as plt


def getSubImageBase64(client,id):
    # print("subImage",id)
    return unpack(client.getR().hget("Camera_Monitor_SubImage",id))

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
def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def loadBase64Image(base64_image):
    image_array =Image.open(io.BytesIO(base64.b64decode(base64_image)))
    return image_array


client=Redis(IP="10.214.131.229",port=6379)

id="container-value-cam1-mechanical-8"
curSubImage=getSubImageBase64(client,id)
LabelData=unpack(client.getR().hget("Label_mechanical",id))
# print(curSubImage)
# print(LabelData.get("image",""))
# print(LabelData.get("points",[]))
# print(LabelData.get("image","")==curSubImage)

source_image=loadBase64Image(LabelData.get("image",""))
new_image=loadBase64Image(curSubImage)
LabelPoints=LabelData.get("points",[])
w,h=source_image.size
target_resolution = (640, 480)
source_image_resized = cv2.resize(source_image, target_resolution)
new_image_resized = cv2.resize(new_image, target_resolution)
# fig, ax = plt.subplots()
# ax.imshow(LabelImage)
# for p in LabelPoints:
#     x=round(p['x']*w)
#     y=round(p['y']*h)
#     ax.plot(x, y, 'bo', markersize=5)
#     ax.annotate(p['tag'], (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)
# plt.axis('off')
# plt.show()