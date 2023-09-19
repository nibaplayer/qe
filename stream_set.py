
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

# 调用函数删除所有流
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

# 调用函数删除具有前缀为 "prefix_" 的所有规则
def delete_rules_with_prefix(prefix):
    url = "http://10.214.131.229:9081/rules"
    response = requests.get(url)
    if response.status_code == 200:
        rules = response.json()
        for rule in rules:
            if rule["id"].startswith(prefix):
                delete_url = url + "/" + rule["id"]
                delete_response = requests.delete(delete_url)
                if delete_response.status_code == 200:
                    print(f"rule {rule['id']} 删除成功")
                else:
                    print(f"rule {rule['id']} 删除失败")
    else:
        print("获取规则列表失败")


def Reg_rule(name):
   id = name 

   url="http://10.214.131.229:9081/rules"

   delete_rules_with_prefix(id)
   
   if "LED" in name:
      i = 1
      status_splited = intervals[name][0].split(",")        #注意如果LED需要多个判断条件要用，隔开
      for status in status_splited:
         temp_id = f"{id}_{i}"
         i += 1
         # status = "'%" + status + "'"
         rules_profile={
            "id": temp_id,
            "sql":f'SELECT id ,name from {name} where name LIKE "%{status}";',#这里参数需要改
            "actions":[
               {
                  "mqtt":{
                     "server":"tcp://10.214.131.229:1883",#这里可以换成变量
                     "topic":"m",#这个“m”用于报警
                  }
               }
            ]
         }
         resp=requests.post(url,json=rules_profile)
         print(resp.content)
         resp=requests.get(url)
         print(resp.content)
   else :
      i = 1
      for interval in intervals[id]:
         interval_splited =  interval.split(",")
         temp_id = f"{id}_{i}"
         i += 1
         rules_profile={
            "id": temp_id,
            "sql":f"SELECT id ,score from {name} \
               where score BETWEEN {interval_splited[0]} AND  {interval_splited[1]};",#这里参数需要改
            "actions":[
               {
                  "mqtt":{
                     "server":"tcp://10.214.131.229:1883",#这里可以换成变量
                     "topic":"m",#这个“m”用于报警
                  }
               }
            ]
         }
         resp=requests.post(url,json=rules_profile)
         print(resp.content)

         resp=requests.get(url)
         print(resp.content)


delete_all_streams()# 调用函数删除所有流

delete_rules_with_prefix("")#把所有规则清空一遍

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
      #拆分放到创建rule中处理
      
      temp = temp.replace("-interval","")
      temp = temp.replace("-","_")
      
      intervals[temp] = temp_intervals.split("&") #字典中的temp为修改后的   -全部替换为_
      #每张表要创建一条流
      
      Reg_stream(temp)
      
      Reg_rule(temp)#创建初始的规则  之后要定期查询更新
   

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
         new_interval = temp_intervals.split("&")
         if new_interval != intervals[temp]:  #当数值更新时
            intervals[temp] = new_interval
            Reg_rule(temp)#更新规则
   print("update checked")
   time.sleep(1) # 每操作一轮休息
