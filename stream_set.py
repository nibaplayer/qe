
import requests
import redis
import time
from db_server import util



dataType={
    "int": "bigint",
    "float": "float",
    "string": "string",
    "bool": "boolean"
}
#这里给每个表注册一个流
def Reg_stream(name):
   url="http://10.214.131.229:9081/streams"
   id = name
   resp=requests.delete(url+"/"+id)
   print(resp.content)
   profile={"sql":f"create stream {id} \
            (id {dataType['int']}, name {dataType['string']}, score {dataType['float']},status {dataType['bool']}) \
            WITH ( datasource = \"{id}\", FORMAT = \"json\", KEY = \"id\")"}
   resp=requests.post(url,json=profile)
   print(resp.content)
   resp=requests.get(url)
   print(resp.content)

def Reg_rule(name):
   id = name 
   rules_profile={
      "id": id,
      "sql":f"SELECT id ,avg(score) from {name} group by TUMBLINGWINDOW(ss, 1) \
         having avg_score BETWEEN {intervals[name][0]} AND {intervals[name][1]};",#这里参数需要改
      "actions":[
         {
            "mqtt":{
               "server":"tcp://10.214.131.229:1883",#这里可以换成变量
               "topic":"m",#这个“m”用于报警
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
      temp_intervals = temp_intervals.replace("inf","100000000") #把默认的inf替换掉
      
      temp = temp.replace("-interval","")
      temp = temp.replace("-","_")
      
      intervals[temp] = temp_intervals.split(",") #字典中的temp为修改后的   -全部替换为_
      #每张表要创建一条流
      
      Reg_stream(temp)
      
      Reg_rule(temp)#创建初始的规则  之后要定期查询更新
   



        # print(temp)
        #r.hset(hash_name,temp,pack("(10,20)"))
# for field in fields:
#     temp = field.decode()
#     if "interval" in temp:
#         print(temp)
#         r.hset(hash_name,temp,pack("(10,20)"))

while True:
   fields = r.hkeys(hash_name)
   for field in fields:
      temp = field.decode()
      if "interval" in temp:
         temp_intervals = util.unpack(r.hget(hash_name,temp))
         temp_intervals = temp_intervals.strip("()")
         temp_intervals = temp_intervals.replace("inf","100000000") #把默认的inf替换掉
         temp = temp.replace("-interval","")
         temp = temp.replace("-","_")
         new_interval = temp_intervals.split(",")
         if new_interval != intervals[temp]:  #当数值更新时
            intervals[temp] = new_interval
            Reg_rule(temp)#更新规则
   print("update checked")
   time.sleep(3) # 每操作一轮休息3秒
