from util import unpack,pack

import redis

r = redis.Redis(host="10.214.131.229",port= 6379)

hash_name = "monitor_profile"
fields = r.hkeys(hash_name)
for field in fields:
    temp = field.decode()
    if "interval" in temp:
        print(temp)
        r.hset(hash_name,temp,pack("(10,20)"))

#value = unpack(r.hget(,"container-value-cam1-mechanical-2-interval"))
temp = unpack(r.hget(hash_name,"container-value-cam1-mechanical-1-interval"))
temp = temp.strip("()")
print(temp)