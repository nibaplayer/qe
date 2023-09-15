import base64
from collections import OrderedDict
import time
import pickle
import base64
import zlib
import redis
import io
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR, draw_ocr
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

def getMaxBoxValue(resultEn,resultCn):
    filtered_data = [item for item in resultEn[0] if isinstance(item[1], (int, float)) or (isinstance(item[1][0], str) and item[1][0].replace('.', '', 1).isdigit())]
    if filtered_data==[]:
        filtered_data = [item for item in resultCn[0] if isinstance(item[1], (int, float)) or (isinstance(item[1][0], str) and item[1][0].replace('.', '', 1).isdigit())]
        if filtered_data==[]:
            return -1.0
    areas = []
    for item in filtered_data:
            points = item[0]
            x = [point[0] for point in points]
            y = [point[1] for point in points]
            area = 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(len(x) - 1)))
            areas.append(area)

    # 找到面积最大的行的cls
    max_area_index = areas.index(max(areas))
    return filtered_data[max_area_index][1][0]
def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))        
client=Redis(IP="10.214.131.229",port=6379)
ocrEn = PaddleOCR(use_angle_cls=True, lang="en")  
ocrCn = PaddleOCR(use_angle_cls=True, lang="ch") 

while(True):
    try:
        ids=unpack(client.getR().get("Monitor_Containers_Id"))
        for id in ids:
            Rpipe = client.getPipe()
            if "digital" in id:
                image=client.getR().hget("Camera_Monitor_SubImage",id)
                if image!=None:
                    base64_image=unpack(image)
                    image_data = base64.b64decode(base64_image)
                    image = Image.open(io.BytesIO(image_data))
                    image_array = np.array(image)
                    resultEn = ocrEn.ocr(image_array,cls=True)
                    resultCn = ocrCn.ocr(image_array,cls=True)
#                    print("resultEn -- resultCn",resultCn,resultEn)
                    value=getMaxBoxValue(resultEn,resultCn)
                    if value==-1:
                        continue
                    Rpipe.hset(f"Monitor_{id}", "value",value)
                    Rpipe.hset(f"Monitor_{id}", "timestamp", getTimeStampStr())
                    print(f"Monitor_{id}", value)
            Rpipe.execute()
    except:
        pass
    time.sleep(10)
