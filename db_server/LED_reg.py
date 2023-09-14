import base64
from collections import OrderedDict
import time
from util import Redis,pack,unpack,CamImage


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
            print(f"Monitor_{id}")
    Rpipe.execute()