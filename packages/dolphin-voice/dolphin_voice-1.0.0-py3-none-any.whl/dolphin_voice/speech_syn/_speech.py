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
from dolphin_voice.speech_syn.parameters import Parameters


class Speech:
    def __init__(self, callback, url):
        self._header = {}
        self._context = {}
        self._payload = {}
        self._token = None
        self._app_id = None
        self._url = url
        self._callback = callback
        self._status = Parameters.STATUS_INIT
        self._ws = None
        self._thread = None
        self._task_id = None

        sdk_info = {Parameters.CONTEXT_SDK_KEY_NAME: Parameters.CONTEXT_SDK_VALUE_NAME,
                    Parameters.CONTEXT_SDK_KEY_VERSION: Parameters.CONTEXT_SDK_VALUE_VERSION}
        self._context[Parameters.CONTEXT_SDK_KEY] = sdk_info

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

    def get_sample_rate(self):
        return self._payload[Parameters.PAYLOAD_KEY_SAMPLE_RATE]

    def set_lang_type(self, lang_type):
        self._payload[Parameters.PAYLOAD_KEY_LANG_TYPE] = lang_type

    def get_lang_type(self):
        return self._payload[Parameters.PAYLOAD_KEY_LANG_TYPE]

    def get_task_id(self):
        return self._header[Parameters.HEADER_KEY_TASK_ID]

    def put_context(self, key, obj):
        self._context[key] = obj

    def add_payload_param(self, key, obj):
        self._payload[key] = obj

    def get_status(self):
        return self._status

    def serialize(self):
        root = {Parameters.HEADER: self._header}

        if len(self._payload) != 0:
            root[Parameters.CONTEXT] = self._context
            root[Parameters.PAYLOAD] = self._payload

        return json.dumps(root)
