
import requests
import redis
from db_server import util


url="http://10.214.131.229:9081/streams"

dataType={
    "int": "bigint",
    "float": "float",
    "string": "string",
    "bool": "boolean"
}
id="mts_stream"
resp=requests.delete(url+"/"+id)
print(resp.content)

profile={"sql":f"create stream {id} (id {dataType['int']}, name {dataType['string']}, score {dataType['float']},status {dataType['bool']}) WITH ( datasource = \"topic/mts\", FORMAT = \"json\", KEY = \"id\")"}

resp=requests.post(url,json=profile)
print(resp.content)

resp=requests.get(url)
print(resp.content)
id="rule1"


#从redis读取阈值
r = redis.Redis(host='10.214.131.229', port=6379)
hash_name = "monitor_profile"
fields = r.hkeys(hash_name) #读取所有fields
for field in fields:
    print(field.decode())
#测试下rules_profile中对于变量的引用
# temp = util.unpack(r.hget(hash_name,"container-value-cam1-mechanical-1-interval"))
# temp = temp.strip("()")
# res = temp.split(",")


rules_profile={
   "id": id,
   "sql":f"SELECT id ,avg(score) as avg_score from mts_stream group by TUMBLINGWINDOW(ss, 1) having avg_score BETWEEN {10} AND {20};",#这里参数需要改
   "actions":[
      {
         "mqtt":{
            "server":"tcp://10.214.131.229:1883",
            "topic":"m",
         }
      }
   ]
}

url="http://10.214.131.229:9081/rules"

resp=requests.delete(url+"/"+id)
print(resp.content)

resp=requests.post(url,json=rules_profile)
print(resp.content)

resp=requests.get(url)
print(resp.content)