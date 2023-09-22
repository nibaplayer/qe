import paho.mqtt.client as mqtt
import json
import redis
from db_server.util import pack, unpack
import base64
from PIL import Image
import io


r = redis.Redis(host='10.214.131.229', port=6379)

hash_name = "monitor_profile"

print(unpack(r.get("Monitor_Containers_Id")))

imgl = r.hgetall("Camera_Monitor_SubImage")

for img in imgl:
    base64_iamge = unpack(imgl[img])
    image_data = base64.b64decode(base64_iamge)
    image = Image.open(io.BytesIO(image_data))
    image.show()