
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
#这里给每个表注册一个流
def Reg_stream(name):
   id = name
   resp=requests.delete(url+"/"+id)
   print(resp.content)
   profile={"sql":f"create stream {id} (id {dataType['int']}, name {dataType['string']}, score {dataType['float']},status {dataType['bool']}) WITH ( datasource = \"topic/{id}\", FORMAT = \"json\", KEY = \"id\")"}
   resp=requests.post(url,json=profile)
   print(resp.content)
   resp=requests.get(url)
   print(resp.content)


id="rule1"





#从redis读取阈值
r = redis.Redis(host='10.214.131.229', port=6379)
hash_name = "monitor_profile"
fields = r.hkeys(hash_name) #读取所有fields 提取阈值
#创建哈希表用于存储阈值
intervals = {}
for field in fields:
   temp = field.decode()
   if "interval" in temp:
      temp_intervals = util.unpack(r.hget(hash_name,temp))
      temp_intervals = temp_intervals.strip("()")
      intervals[temp] = temp_intervals.split(",")
      #每张表要创建一条流
      temp = temp.replace("-interval","")
      Reg_stream(temp)
   



        # print(temp)
        #r.hset(hash_name,temp,pack("(10,20)"))
# for field in fields:
#     temp = field.decode()
#     if "interval" in temp:
#         print(temp)
#         r.hset(hash_name,temp,pack("(10,20)"))



rules_profile={
   "id": id,
   "sql":f"SELECT id ,avg(score) as avg_score from mts_stream group by TUMBLINGWINDOW(ss, 1) having avg_score BETWEEN {intervals['container-value-cam1-mechanical-1-interval'][0]} AND {intervals['container-value-cam1-mechanical-1-interval'][1]};",#这里参数需要改
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