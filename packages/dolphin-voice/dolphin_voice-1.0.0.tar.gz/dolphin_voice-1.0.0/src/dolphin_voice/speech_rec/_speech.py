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

import json
import platform
from dolphin_voice.speech_rec.parameters import Parameters


class Speech:
    def __init__(self, callback, url):
        self._header = {}
        self._context = {}
        self._payload = {}
        self._environment = {}
        self._token = None
        self._app_id = None
        self._url = url
        self._callback = callback
        self._status = Parameters.STATUS_INIT
        self._ws = None
        self._thread = None
        self._task_id = None

    def set_app_id(self, app_id):
        self._app_id = app_id

    def get_app_id(self):
        return self._app_id

    def set_token(self, token):
        self._token = token

    def get_token(self):
        return self._token

    def set_format(self, format):
        self._payload[Parameters.PAYLOAD_KEY_FORMAT] = format

    def get_format(self):
        return self._payload[Parameters.PAYLOAD_KEY_FORMAT]

    def set_sample_rate(self, sample_rate):
        self._payload[Parameters.PAYLOAD_KEY_SAMPLE_RATE] = sample_rate

    def set_audio_url(self,audio_url):
        self._payload[Parameters.PAYLOAD_KEY_AUDIO_URL] = audio_url

    def get_audio_url(self):
        return self._payload[Parameters.PAYLOAD_KEY_AUDIO_URL]

    def set_audio_field(self,field):
        self._payload[Parameters.PAYLOAD_KEY_FIELD] = field

    def set_enable_save_log(self,flag=False):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_SAVE_LOG] = flag

    def get_audio_field(self):
        return self._payload[Parameters.PAYLOAD_KEY_FIELD]

    def set_lang_type(self, lang_type):
        self._payload[Parameters.PAYLOAD_KEY_LANG_TYPE] = lang_type

    def get_lang_type(self):
        return self._payload[Parameters.PAYLOAD_KEY_LANG_TYPE]

    def get_sample_rate(self):
        return self._payload[Parameters.PAYLOAD_KEY_SAMPLE_RATE]

    def get_task_id(self):
        return self._header[Parameters.HEADER_KEY_TASK_ID]

    def add_payload_param(self, key, obj):
        self._payload[key] = obj

    def get_status(self):
        return self._status

    def set_speaker_id(self, data, **kwargs):
        if kwargs:
            kwargs[Parameters.PAYLOAD_KEY_SPEAKER_ID] = data
            self._payload = kwargs
        else:
            self._payload[Parameters.PAYLOAD_KEY_SPEAKER_ID] = data

    def serialize(self):
        root = {Parameters.HEADER: self._header}

        if len(self._payload) != 0:
            root[Parameters.PAYLOAD] = self._payload

        return json.dumps(root)
