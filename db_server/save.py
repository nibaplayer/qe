import base64
import time

from util import Redis,pack,unpack

def getTimeStampStr():
    timestamp = int(time.time())
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def check_in_range(number, range_str):
    def check_in_srange(number, range_str):
        if range_str.startswith('('):
            start_inclusive = False
        elif range_str.startswith('['):
            start_inclusive = True
        else:
            raise ValueError("Invalid range format")

        if range_str.endswith(')'):
            end_inclusive = False
        elif range_str.endswith(']'):
            end_inclusive = True
        else:
            raise ValueError("Invalid range format")

        start_str, end_str = map(str.strip, range_str[1:-1].split(','))

        start = float(start_str) if start_str != "-inf" else float('-inf')
        end = float(end_str) if end_str != "inf" else float('inf')

        if start_inclusive:
            if number < start:
                return False
        else:
            if number <= start:
                return False

        if end_inclusive:
            if number > end:
                return False
        else:
            if number >= end:
                return False

        return True
    result,waitch=False,range_str.split("&")
    for wch in waitch:
        result |= check_in_srange(number,wch)
    return result

cams=["cam1","cam2","cam4"]

nameCN=["指针式仪表","数字式仪表"]
nameEN=["mechanical","digital"]
dashboardNum=2
Monitor_Camera_Head={}

container_keys=["value","timestamp","interval","frequency","xin","xmax","ymin","ymax","scale"]
container_default_value=[0,getTimeStampStr(),"(1,2)",1,0,100,0,100,100]

for cam in cams:
    Monitor_Camera_Head[cam] = []
    for cpt,(c,e) in enumerate(zip(nameCN,nameEN)):
        Monitor_Camera_Head[cam].append({
            "name": c,
            "id": e,
            "dashboardes": []
        })
        for i in range(dashboardNum):
            Monitor_Camera_Head[cam][cpt]["dashboardes"].append({
                "name": "表"+str(i+1),
                "id": str(i+1)
            })

print(Monitor_Camera_Head)
# Monitor_Camera_Head={
#     "cam1": [{
#         "name": "指针式仪表",
#         "id": "mechanical",
#         "dashboardes": [{
#             "name": "表1",
#             "id": "1"
#         },{
#             "name": "表2",
#             "id": "2"
#         }]
#     },{
#         "name": "数字式仪表",
#         "id": "digital",
#         "dashboardes": [{
#             "name": "表1",
#             "id": "1"
#         },{
#             "name": "表2",
#             "id": "2"
#
#         }]
#     }],
#     "cam2": [{
#         "name": "指针式仪表",
#         "id": "mechanical",
#         "dashboardes": [{
#             "name": "表1",
#             "id": "1"
#         },{
#             "name": "表2",
#             "id": "2"
#         }]
#     },{
#         "name": "数字式仪表",
#         "id": "digital",
#         "dashboardes": [{
#             "name": "表1",
#             "id": "1"
#         },{
#             "name": "表2",
#             "id": "2"
#         }]
#     }]
# }

r=Redis(IP="10.214.131.229",port=6379)
client=r.getR()

for k,v in Monitor_Camera_Head.items():
    client.hset("Monitor_Camera_Head",k,pack(v))


with open('templates/image/1.jpg', 'rb') as f:
    image_data = f.read()
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    pack_image=pack(encoded_image)
    for cam in cams:
        for cpt,(c,e) in enumerate(zip(nameCN,nameEN)):
            for i in range(dashboardNum):
                id=f"container-value-{cam}-{e}-{i+1}"
                print(id)
                client.hset("Camera_Monitor_SubImage",id,pack_image)
                client.hset(f"Monitor_{id}","id",f"{cam}-{e}-{i+1}")
                for ck,cv in zip(container_keys,container_default_value):
                    client.hset(f"Monitor_{id}",ck,cv)


def getMonitor_Camera_Head():
    data=client.hgetall("Monitor_Camera_Head")
    Monitor_Camera_Head=[]
    for k,v in data.items():
        k,v=str(k,'utf-8'),unpack(v)
        Monitor_Camera_Head.append({
            "name": k,
            "classes": v
        })
    return Monitor_Camera_Head

def getCamera_Names(client):
    data=client.hgetall("Monitor_Camera_Head")
    cameras=data.keys()
    cameras=[str(cam,"utf-8") for cam in cameras]
    return cameras

print(getCamera_Names(client))


Rpipe=r.getPipe()
Rpipe.hget("Monitor_container-value-cam2-mechanical-1","value")
Rpipe.hget("Monitor_container-value-cam2-mechanical-1","timestamp")
Rpipe.hget("Monitor_container-value-cam2-mechanical-1","interval")
v,ts,interval=Rpipe.execute()
v=float(v)
ts=str(ts,'utf-8')
interval=str(interval,'utf-8')
print(v,ts,interval)

print(check_in_range(2.1,"(0,1)&(2,3)"))

container_ids=[]
for cam,v in Monitor_Camera_Head.items():
    for cls in v:
        dbs=cls.get("dashboardes",{})
        cls_id=cls.get("id","")
        for db in dbs:
            id=db.get("id","")
            if id !="":
                container_ids.append(f"container-value-{cam}-{cls_id}-{id}")





def upload_image(client, cam_id):
    CHUNK_SIZE = 1024  # 每个片的大小为1KB
    lastIndex=1
    # 读取图片数据
    with open("templates/image/8Pressures.jpg", 'rb') as file:
        image_data = file.read()

    # 计算总片数
    total_slices = (len(image_data) + CHUNK_SIZE - 1) // CHUNK_SIZE

    # 上传图片切片
    for i in range(total_slices):
        # 获取当前切片的起始位置和结束位置
        start = i * CHUNK_SIZE
        end = start + CHUNK_SIZE

        # 切片数据
        slice_data = image_data[start:end]

        # 将切片数据进行 Base64 编码
        encoded_slice = base64.b64encode(slice_data).decode()

        # 构建 Redis 哈希表的键名
        hash_name = f'cam{cam_id}_{lastIndex}'

        # 将切片数据存储到 Redis 中
        client.hset(hash_name, i, encoded_slice)

    # 更新最新索引

    client.set(f'cam{cam_id}_latest', lastIndex)

upload_image(client,"5")

rectangles = [[0.2864583333333333, 0.45955882352941174, 0.31862745098039214, 0.5020424836601307, '1'], [0.46660539215686275, 0.4579248366013072, 0.4963235294117647, 0.49836601307189543, '2'], [0.6596200980392157, 0.4497549019607843, 0.6896446078431373, 0.4897875816993464, '3'], [0.8403799019607843, 0.4334150326797386, 0.8786764705882353, 0.48080065359477125, '4'], [0.2818627450980392, 0.5126633986928104, 0.31495098039215685, 0.5575980392156863, '5'], [0.4675245098039216, 0.502859477124183, 0.4996936274509804, 0.5449346405228758, '6'], [0.6580882352941176, 0.4963235294117647, 0.6933210784313726, 0.5428921568627451, '7'], [0.8480392156862745, 0.49468954248366015, 0.8875612745098039, 0.5453431372549019, '8']]
recLen=len(rectangles)
for i in range(recLen):
    rectangles[i].append(0.0)
client.hset("camera_boxes",str(5),pack(rectangles))