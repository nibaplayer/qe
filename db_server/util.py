from io import BytesIO

import redis
import time
import requests
import yaml
from os.path import join
import pickle
import base64
import zlib

from PIL import Image

REDIS_IP="10.214.131.229"
REDIS_PORT=6379



def pack(v):
    return zlib.compress(base64.b64encode(pickle.dumps(v)))

def unpack(v):
    return pickle.loads(base64.b64decode(zlib.decompress(v)))

class Redis:
    def __init__(self, IP=REDIS_IP, port=REDIS_PORT):
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

class CamImage:
    maxUpdateImageSizePt=10
    updateImageSizePt=0
    ImageWidthPer = {}

    def _fix_base64_padding(self,base64_str):
        missing_padding = 4 - (len(base64_str) % 4)
        base64_str += "=" * missing_padding
        return base64_str

    def _fetch_redis_hash(self,client,cam_id):
        latest_index = int(client.getR().get("cam"+str(cam_id)+"_latest"))
    #     print(latest_index)
        hash_name = 'cam' + str(cam_id) + '_'
        hash_data = client.getR().hgetall(hash_name + str(latest_index))
        hash_data = {key.decode(): value.decode() for key, value in hash_data.items()}
        if "total" not in hash_data.keys():
            hash_data["total"]=len(hash_data.values())
        return hash_data

    def Get(self,client,cam_id):
        hash_data = self._fetch_redis_hash(client, cam_id)
        total = int(hash_data["total"])
        combined_image_data = b''  # 存储图像数据
        for i in range(total):
            combined_image_data += base64.b64decode(self._fix_base64_padding(hash_data[str(i)]))
        image_data=base64.b64encode(combined_image_data).decode('utf-8')
        return image_data

    def GetBytes(self,client,cam_id):
        hash_data = self._fetch_redis_hash(client, cam_id)
        total = int(hash_data["total"])
        combined_image_data = b''  # 存储图像数据
        for i in range(total):
            combined_image_data += base64.b64decode(self._fix_base64_padding(hash_data[str(i)]))
        return combined_image_data


    def GetWidthPer(self,client,cam_id):
        if self.updateImageSizePt == 0:
            self.updateImageSizePt = self.maxUpdateImageSizePt
            w,h=Image.open(BytesIO((self.Get(client,cam_id)))).size
            self.ImageWidthPer[cam_id] = float(h)/w
        else:
            self.updateImageSizePt -= 1
        wp = self.ImageWidthPer.get(cam_id, 1.0)


        return f"{wp*100}%"


def flush_db():
    r = Redis(REDIS_IP, REDIS_PORT)
    r.getR().flushall()
    time.sleep(1)
    r.close()