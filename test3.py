import requests
import json

def delete_all_streams():
    url = "http://10.214.131.229:9081/streams"
    response = requests.get(url)
    if response.status_code == 200:
        streams = response.json()
        for stream in streams:
            delete_url = url + "/" + stream
            # print(delete_url)
            delete_response = requests.delete(delete_url)
            if delete_response.status_code == 200:
                print(f"stream {stream} 删除成功")
            else:
                print(f"stream {stream} 删除失败")
    else:
        print("获取流列表失败")

# 调用函数删除所有流
# delete_all_streams()

url = "http://10.214.131.229:9081/rules"
response = requests.get(url)
print(response.json())
for temp in response.json():
    if "id" in temp:
        print(temp)
