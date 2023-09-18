from util import unpack,pack

import redis

r = redis.Redis(host="10.214.131.229",port= 6379)

hash_name = "monitor_profile"
fields = r.hkeys(hash_name)
#创建哈希表用于存储阈值
intervals = {}
for field in fields:
    temp = field.decode()
    if "interval" in temp:
        temp_intervals = unpack(r.hget(hash_name,temp))
        temp_intervals = temp_intervals.strip("()")
        intervals[temp] = temp_intervals.split(",")
        # print(temp)
        # r.hset(hash_name,temp,pack("(10,30)"))
        print(temp,unpack(r.hget(hash_name,temp)))
# r.hset(hash_name,"container-value-cam1-digital-5-interval",pack("(10,30)"))

print(intervals)
#value = unpack(r.hget(,"container-value-cam1-mechanical-2-interval"))
# temp = unpack(r.hget(hash_name,"container-value-cam1-mechanical-1-interval"))
# temp = temp.strip("()")
# print(temp)

# print(intervals["container-value-cam1-mechanical-1-interval"][0],intervals["container-value-cam1-mechanical-1-interval"][1])
# ids = unpack(r.get("Monitor_Containers_Id"))
# for id in ids:
#     print(id)