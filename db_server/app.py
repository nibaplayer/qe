import base64
import csv
import io
from PIL import Image
from flask import Flask, render_template,request,jsonify
from collections import OrderedDict
import time
from util import Redis,pack,unpack,CamImage

app = Flask(__name__, static_folder='templates')
client=Redis(IP="10.214.131.229",port=6379)
csv_path="output.csv"
csv_path_head = 'output/'
width, height,ppt=1,1,0
points=[]
Cams=CamImage()
with open(r'd:\code\qe\db_server\templates\image\none_image.jpg', 'rb') as f:
    image_data = f.read()
    None_image = base64.b64encode(image_data).decode('utf-8')
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
        cam,v =str(cam,'utf-8'),unpack(v)
        # print(cam,v)
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

def getCamera_Names(client):
    data=client.getR().hgetall("Monitor_Camera_Head")
    cameras=data.keys()
    cameras=[str(cam,"utf-8") for cam in cameras]
    return cameras.sort()

def getSubImageBase64(client,id):
    # print("subImage",id)
    try:
        return unpack(client.getR().hget("Camera_Monitor_SubImage",id))
    except:
        return None_image

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

def getMonitorContainerValue(client,id):
    Rpipe = client.getPipe()
    print(f"Monitor_{id}")
    Rpipe.hget(f"Monitor_{id}", "value")
    Rpipe.hget(f"Monitor_{id}", "timestamp")
    Rpipe.hget(f"Monitor_{id}", "interval")
    v, ts, interval = Rpipe.execute()
    if nameEN[0] in id or nameEN[1] in id:
        if v==None:
            v=-1.0
        else:
            v=float(v)
        if interval==None:
            interval="(0,0)"
        else:
            interval = str(interval, 'utf-8')
    else:
        if v==None:
            v="None"
        else:
            v=str(v,'utf-8')
        if interval==None:
            interval="None"
        else:
            interval=str(v,'utf-8')
    if ts ==None:
        ts="NULL"
    else:
        ts=str(ts, 'utf-8')
    if interval=="None" or interval=="(0,0)":
        return v,ts,interval,False
    return v,ts,interval,check_in_range(v,interval)




@app.route('/')
def index():
    Monitor_Camera_Head=getMonitor_Camera_Head(client)
    timestamp=getTimeStampStr()
    return render_template("overview_index.html",cameraes=Monitor_Camera_Head,timestamp=timestamp)

@app.route('/setting')
def setting():
    Monitor_Camera_Head = getMonitor_Camera_Head(client)
    timestamp=getTimeStampStr()
    return render_template("setting_index.html",cameraes=Monitor_Camera_Head,timestamp=timestamp)

@app.route('/camera/<camid>')
def camera(camid):
    image_data=Cams.Get(client,camid)
    return render_template("camera_monitor.html",image_data=image_data,camid=camid)


@app.route('/getDbMonitor', methods=['POST'])
def get_db_monitor():
    # 获取请求数据
    data = request.get_json()
    id = data.get('id')
    valueId,dbId=dbId2valueId(id)
    v, ts, interval,ch=getMonitorContainerValue(client,valueId)
    result={
        f"{valueId}-value": f'<p class="{"red" if ch else "green"}-text">{v}</p>',
        f"{valueId}-timestamp": ts,
        f"{valueId}-interval": interval
    }
    return jsonify(result)

@app.route('/getImage', methods=['POST'])
def get_image():
    data = request.get_json()
    id = data.get('id')
    valueId, _ = dbId2valueId(id)
    # 假设你的 base64 图片数据存储在变量 image_data 中

    result={
        "id": f"{valueId}-image",
        "image": getSubImageBase64(client,valueId)
    }
    return jsonify(result)

@app.route('/getBoxes/<camid>')
def getBoxes(camid):
    data=client.getR().hget("camera_boxes",camid)
    if data!=None:
        boxes=unpack(data)
    else:
        boxes=[]
    return jsonify(boxes)


@app.route('/getContainerIds', methods=['POST','GET'])
def get_ContainerIds():
    result=client.getR().get("Monitor_Containers_Id")
    return jsonify(unpack(result))

@app.route("/updateSettingProfile",methods=["POST"])
def updateSettingProfile():
    data = request.json
    buttons={}
    Rpipe=client.getPipe()
    for k,v in data.items():
        if "button" not in k:
            Rpipe.hset("monitor_profile",k,pack(v))
            #输出测试
            print(k,v)
            
        else:
            buttons[k]=v
    for k,v in buttons.items():
        Rpipe.hset("monitor_profile_button",k,pack(v))
    Rpipe.execute()
    response = {'message': 'Setting updated successfully'}
    return jsonify(response)

@app.route("/getSettingProfile",methods=["POST","GET"])
def getSettingProfile():
    mp=client.getR().hgetall("monitor_profile")
    result = {}
    for k, v in mp.items():
        result[str(k, 'utf-8')] = unpack(v)
    return jsonify(result)

@app.route("/getSettingProfileButton",methods=["POST","GET"])
def getSettingProfileButton():
    mpb=client.getR().hgetall("monitor_profile_button")
    result = {}
    for k, v in mpb.items():
        result[str(k, 'utf-8')] = unpack(v)
    return jsonify(result)


@app.route("/label/setting_image/<id>")
def label_setting_image(id):
    base64_image=getSubImageBase64(client,id[:-6])
    global width, height
    width, height=Image.open(io.BytesIO(base64.b64decode(base64_image))).size
    width, height =float(width),float(height)
    return render_template("SubImage_label.html",image_data=base64_image,camid=id)

@app.route('/handle_click/<camid>', methods=['POST'])
def handle_click(camid):
    global width, height
    data = request.get_json()
    x = data['x']
    y = data['y']
    points.append({'x': x/width, 'y': y/height, 'tag': None})  # 将点击过的点的坐标和标签存储起来
    return jsonify({'success': True})

@app.route('/save_points/<camid>', methods=['POST'])
def save_points(camid):
    global points,ppt
    data = request.get_json()
    tag = data['tag']
    while len(points)<=ppt:
        time.sleep(0.1)
    # 更新最后一个点击点的标签
    points[ppt]['tag'] = tag
    ppt+=1
    return jsonify({'success': True})

@app.route('/get_points/<camid>', methods=['GET'])
def get_points(camid):
    return jsonify(points)

@app.route('/save_all_points/<camid>', methods=['POST'])
def save_all_points(camid):
    global points,ppt
    time.sleep(1)
    while ppt<len(points):
        time.sleep(0.1)
    label={
        "image": getSubImageBase64(client,camid[:-6]),
        "points": points
    }
    print("Label_mechanical", camid[:-6], label)
    client.getR().hset("Label_mechanical",camid[:-6],pack(label))

    points = []  # 清空点击点列表
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15000)
