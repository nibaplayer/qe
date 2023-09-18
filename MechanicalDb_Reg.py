import sys
sys.path.append("segment-anything/")
import base64
import time
import pickle
import base64
import zlib
import redis
import io
import numpy as np
from PIL import Image
from segment_anything import SamPredictor, sam_model_registry
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import json


def showMasks(masks):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    # 循环显示每个通道的矩阵
    for i in range(3):
        axes[i].imshow(masks[i], cmap='binary', interpolation='none')
        axes[i].set_axis_off()  # 隐藏坐标轴和刻度
    # 显示图形
    plt.show()

def pack(v):
    return zlib.compress(base64.b64encode(pickle.dumps(v)))

def unpack(v):
    return pickle.loads(base64.b64decode(zlib.decompress(v)))

def mvAxis(points,center):
    # 坐标转换
    n_points=[]
    for pt in points:
        x,y=pt
        x-=center[0]
        y-=center[1]
        y*=-1
        n_points.append((x,y))
    return n_points

def stdAngleAbs(p,slope=None):
    x,y=p
    if slope==None:
        if x>0:
            return (np.arctan(y/x)*(180/np.pi)+360)%360
        elif x==0:
            if y>0:
                return 90
            else:
                return 270
        else:
            return np.arctan(y/x)*(180/np.pi)+180
    else:
        if slope==0:
            if y>0:
                return 90
            else:
                return 270
        else:
            angle=np.arctan(slope)*(180/np.pi)
            if x>0:
                return (angle+360)%360
            else:
                return angle+180

def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))   

def getCenterLine(img, point, direction="up"):
    if direction == "up":
        dy = -1
    else:
        dy = 1
    cy, cx = point  # 后面是先后x
    points = []
    minx, maxx = cx, cx
    while True:
        while img[minx][cy] or img[maxx][cy]:
            if img[minx][cy]:
                minx -= 1
            if img[maxx][cy]:
                maxx += 1
        points.append(((minx + maxx) / 2, cy))
        cy += dy
        cx = int(points[-1][0])
        if img[cx][cy] or img[cx - 1][cy] or img[cx + 1][cy]:
            minx, maxx = cx - 1, cx + 1
        else:
            break
    n_points = mvAxis(points, points[0])
    if len(n_points) == 1:
        return points, -1, 1
    # 拟合
    x_values = np.array([item[0] for item in n_points])
    y_values = np.array([item[1] for item in n_points])
    slope, _ = np.polyfit(x_values, y_values, 1)
    return points[0], stdAngleAbs(n_points[-1], slope), len(n_points)

class MDB:
    def __init__(self,id="",fpath="",shape=(1,1),MaxValue=1):
        self.fpath=fpath
        self.profile={"values":{}}
        self.loadProfile(id=id,shape=shape)
        self.getPoly()
        self.MaxValue=MaxValue
        self.id=id
        self.shape=shape

    def loadProfile(self,id="",shape=(1,1)):
        w,h=shape
        if client.getR().hexists("Label_mechanical",id):
            self.profile={"values":{}}
            if not client.getR().hexists("Label_mechanical_profile",id):
                labels=unpack(client.getR().hget("Label_mechanical",id))
                
                for lp in labels["points"]:
                    k=float(lp["tag"])
                    if k<0:
                        if k not in self.profile.keys():
                            self.profile[k]=(int(lp['x']*w),int(lp['y']*h))
                    else:
                        if k not in self.profile["values"].keys():
                            self.profile["values"][k]=(int(lp['x']*w),int(lp['y']*h))
                client.getR().hset("Label_mechanical_profile",id,pack(self.profile))
                
            else:
                self.profile=unpack(client.getR().hget("Label_mechanical_profile",id))
            self.setCenter(self.profile.get(-2.0,(0,0)))

    def setCenter(self,center):
        self.center=center

    def getPoly(self):
        vl = list(self.profile["values"].values())
        mvl = mvAxis(vl, self.center)
        angles = []
        for point in mvl:
            angles.append(stdAngleAbs(point))
        x, y = [], list(self.profile["values"].keys())
        for a in angles:
            x.append((360 + angles[0] - a) % (360))
        x[0] = 0
        l = len(x)
        count = int(l * 2 / 3)
        x = np.array(x)
        y = np.array(y)
        coefficients = np.polyfit(x, y, count)
        self.poly = np.poly1d(coefficients)
        self.angleBase=360+angles[0]

    def solve(self,img):
        center_up,angle_up,l_up=getCenterLine(img,self.center,direction="up")
        center_down,angle_down,l_down = getCenterLine(img, self.center, direction="down")
        if l_up==1 and l_down==1:
            return "None"
        if l_up>=l_down:
            center,angle=center_up,angle_up
        else:
            center, angle=center_down, angle_down
            
        self.setCenter(center)
        return self.__solve(angle)

    def __solve(self,angel):
        angel=(self.angleBase-angel)%360
        return self.poly(angel)*self.MaxValue

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
        
sam = sam_model_registry["vit_h"](checkpoint="segment-anything/sam_vit_h_4b8939.pth")

client=Redis(IP="10.214.131.229",port=6379)
predictor = SamPredictor(sam)
        
        
        

ids=unpack(client.getR().get("Monitor_Containers_Id"))
mdbDict={}
while True:
    try:
        for id in ids:
            Rpipe = client.getPipe()
            if "mechanical" in id:
                if not (client.getR().hexists("Label_mechanical",id) or client.getR().hexists("Label_mechanical_profile",id)):
                    continue
                image=client.getR().hget("Camera_Monitor_SubImage",id)
                if image!=None:
                    base64_image=unpack(image)
                    image_data = base64.b64decode(base64_image)
                    image = Image.open(io.BytesIO(image_data))
                    image_array = np.array(image)
                if id not in mdbDict.keys():
                    mdbDict[id]=MDB(id=id,shape=image_array.shape[:2])
                predictor.set_image(image_array)

                masks, _, _ = predictor.predict(point_coords=np.array([[mdbDict[id].center[0],mdbDict[id].center[1]]]),point_labels=np.array([1]))
                showMasks(masks)
                value=mdbDict[id].solve(masks[1])
                if value==-1:
                        continue
                scale=unpack(client.getR().hget("monitor_profile",f"{id}-scale"))
                Rpipe.hset(f"Monitor_{id}", "value",f"{float(scale)*value: .4f}")
                Rpipe.hset(f"Monitor_{id}", "timestamp", getTimeStampStr())
                value=Rpipe.hget(f"Monitor_{id}", "value").decode()
                print(f"Monitor_{id}",value)
                id = id.replace("-","_")
                data={
                    "id": id,
                    "name": "mts",
                    "score": float(value),
                    "status": True
                }
                send2mqtt(id, data, broker_address, port)
                #print(id, data, broker_address, port)
                Rpipe.execute()
    except:
        pass
    time.sleep(10) 
                        
