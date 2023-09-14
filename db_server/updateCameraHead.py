import base64
from collections import OrderedDict
import time
from util import Redis,pack,unpack,CamImage
from io import BytesIO
from PIL import Image

client=Redis(IP="10.214.131.229",port=6379)
Cams=CamImage()
nameCN=["指针式仪表","数字式仪表","LED指示灯"]
nameEN=["mechanical","digital","LED"]


def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def dbId2valueId(dbId):
    parts = dbId.split('-')
    container = parts[0]
    dashboard = '-'.join(parts[2:-1])
    value = parts[-1]
    valueId = f"{container}-value-{dashboard}-{value}"
    return valueId,value

def resetContainerName(client,Monitor_Camera_Head):
    container_ids = []
    for cam, v in Monitor_Camera_Head.items():
        for cls in v:
            dbs = cls.get("dashboardes", {})
            cls_id = cls.get("id", "")
            for db in dbs:
                id = db.get("id", "")
                if id != "":
                    container_ids.append(f"container-value-{cam}-{cls_id}-{id}")
    client.getR().set("Monitor_Containers_Id",pack(container_ids))


def getMonitor_Camera_Head(client):
    data=client.getR().hgetall("Monitor_Camera_Head")
    data=OrderedDict(sorted(data.items(), key=lambda x: x[0]))
    Monitor_Camera_Head=[]
    for k,v in data.items():
        k,v=str(k,'utf-8'),unpack(v)
        Monitor_Camera_Head.append({
            "name": k,
            "classes": v
        })
    resetContainerName(client,data)
    return Monitor_Camera_Head

def getSubImage(camid,box):
    flag,base64_data=True,""
    while flag:
        try:
            CamImage = Image.open(BytesIO(Cams.GetBytes(client, camid)))
            w, h = CamImage.size
            left = round(box[0] * w)
            top = round(box[1] * h)
            right = round(box[2] * w)
            bottom = round(box[3] * h)
            subimage = CamImage.crop((left, top, right, bottom))
            buffered = BytesIO()
            subimage.save(buffered, format="JPEG")
            base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            flag=False
        except:
            pass
    return base64_data

# print(getMonitor_Camera_Head(client))
while True:
    boxesBase=client.getR().hgetall("camera_boxes")
    Monitor_Camera_Head={}
    for k,v in boxesBase.items():
        camid=str(k,"utf-8")
        Camera_Head= [{},{},{}]
        boxes=unpack(v)

        for box in boxes:
            id,cls=box[4],round(box[5])
            if Camera_Head[cls]=={}:
                Camera_Head[cls]={
                    "name": nameCN[cls],
                    "id": nameEN[cls],
                    "dashboardes": []
                }
            db={
                "name": "表"+str(len(Camera_Head[cls]["dashboardes"])+1),
                "id": id
            }
            Camera_Head[cls]["dashboardes"].append(db)
            client.getR().hset("Camera_Monitor_SubImage",f"container-value-cam{camid}-{nameEN[cls]}-{id}",pack(getSubImage(camid,box)))
        Camera_Head=[item for item in Camera_Head if item!={}]
        Monitor_Camera_Head["cam"+camid]=Camera_Head
        resetContainerName(client,Monitor_Camera_Head)
        client.getR().hset("Monitor_Camera_Head", "cam" + camid, pack(Camera_Head))
    time.sleep(30)

print(unpack(client.getR().get("Monitor_Containers_Id")))