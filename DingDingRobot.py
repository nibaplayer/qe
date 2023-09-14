import base64
import hashlib
import hmac
import time
import urllib
import json
from datetime import datetime, timedelta, timezone

import requests



class DingTalk_Base(object):
    def __init__(self):
        webhook = f"https://oapi.dingtalk.com/robot/send?access_token=822317ba3125f4415a53f1f8cba8e79ef186fa3fe4f4cde97f001580aefe0b14"
        secret = r'SEC3a5eee0382ecc74ecd3ecb1e781a2b49793526e805dde80f71bc19c1052e2c1c'
        self.__headers = {'Content-Type': 'application/json;charset=utf-8'}
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        urll=webhook+'&timestamp={}&sign={}'
        self.url =urll.format(timestamp, sign)

    def send_msg(self, title,imageUrl):
        json_text = {
            "msgtype": "markdown",
            "markdown": {
                "title":title,
                "text": title+"\n![screenshot]("+imageUrl+")\n"
            },
            "at": {
                "atMobiles": [
                    ""
                ],
                "isAtAll": False
            }
        }
        return requests.post(self.url, json.dumps(json_text), headers=self.__headers).content

def phraseUrl(s):
    return "http://47.111.141.133:20109/image/"+s+".png"

dd = DingTalk_Base()
