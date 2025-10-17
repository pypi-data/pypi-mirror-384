# -*- coding: utf-8 -*-

"""
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

import requests
import hashlib
import hmac
import base64
import time
import uuid
import json
from cryptography.fernet import Fernet
import dolphin_voice.speech_rec as speech_rec
from dolphin_voice.speech_rec._log import _log
from dolphin_voice.speech_rec.parameters import Parameters


class Token:
    @staticmethod
    def get_token(app_id, app_secret,PRO_ENVIRONMENT=True):
        speech_rec.SpeechClient.set_log_level('INFO')
        if PRO_ENVIRONMENT:
            url = b'gAAAAABmkJNzbGeL8teD2n9o7OCO0udjBBqlhhwDmTXvJtLqPnk-25Ij3knfbNP-ud4UX1fp8GsLDu1PhwXhzNuPCHCJ4tfUTRKrDQtghOb0geZycSiIHmRiUQogcGaMJtrL5550AZtEln6VG2UjBJTF29d-S6OXdw=='
        else:
            url = b'gAAAAABmkJNzbGeL8teD2n9o7OCO0udjBBqlhhwDmTXvJtLqPnk-25Ij3knfbNP-ud4UX1fp8GsLDu1PhwXhzNuPCHCJ4tfUTRKrDQtghOb0geZycSiIHmRiUQogcGaMJtrL5550AZtEln6VG2UjBJTF29d-S6OXdw=='

        headers = {'Content-Type': 'application/json'}
        t = time.time()
        timestamp = int(t)
        timestamp_str = str(timestamp)
        uuid1 = uuid.uuid1()
        signature_nonce = str(uuid1)
        string_to_sign = "app_id="+app_id+"&secret="+app_secret+"&timestamp="+timestamp_str
        def _hmac_sha1(secret, data):
            return str(base64.b64encode(hmac.new(bytes(secret, 'utf-8'), bytes(data, 'utf-8'),
                                                 hashlib.sha1).digest()), 'utf-8')
        signature = _hmac_sha1(app_secret, string_to_sign)
        payload = {Parameters.TOKEN_APP_ID: app_id,
                   Parameters.TOKEN_TIMESTAMP: timestamp,
                   Parameters.TOKEN_SIGNATURE_NONCE: signature_nonce,
                   Parameters.TOKEN_SIGNATURE: signature
                   }
        context="WfrSO5q_QEzr4MY6_wjeB9TEMXTti0aWEE4IVOSHTuY="
        cipher_suite = Fernet(context)
        url = cipher_suite.decrypt(url).decode()
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        res = r.json()
        if int(res.get(Parameters.TOKEN_STATUS)) < 400:
            data = res.get(Parameters.TOKEN_DATA)
            token = data.get(Parameters.TOKEN_APP_TOKEN)
            expire_time = data.get(Parameters.TOKEN_EXPIRE_TIME)
            if expire_time:
                print('Beijing time of token validity：%s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time))))
            return token, expire_time
        _log.error(res.get(Parameters.TOKEN_MESSAGE))
        return None, None
