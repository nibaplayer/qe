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

from paddleocr import PaddleOCR, draw_ocr
ocr = PaddleOCR(use_angle_cls=True, lang="ch")  # need to run only once to download and load model into memory
img_path = 'figure/db2.jpg'
result = ocr.ocr(img_path, cls=True)

def getMaxBoxValue(result):
    filtered_data = [item for item in result if isinstance(item[1], (int, float)) or (isinstance(item[1][0], str) and item[1][0].replace('.', '', 1).isdigit())]
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

print(filtered_data)
print(max_area_cls)