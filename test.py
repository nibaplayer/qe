import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("m")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("10.214.131.229", 1883)

client.loop_forever()