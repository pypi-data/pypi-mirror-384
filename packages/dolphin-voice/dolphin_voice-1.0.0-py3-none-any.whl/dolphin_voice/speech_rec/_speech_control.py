# -*- coding: utf-8 -*-

"""
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *software
 * Unless required by applicable law or agreed to in writing,
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

import websocket
from dolphin_voice.speech_rec._log import _log
from dolphin_voice.speech_rec.parameters import Parameters
from dolphin_voice.speech_rec._speech import Speech
from dolphin_voice.speech_rec.parameters import DefaultParameters


class SpeechControl(Speech):

    def __init__(self, callback, url):
        super(SpeechControl, self).__init__(callback, url)
        self._last_start_retry = False
        self._connected = False
        self._header[Parameters.HEADER_KEY_NAMESPACE] = None
        self._payload[Parameters.PAYLOAD_KEY_FORMAT] = DefaultParameters.MP3
        self._payload[Parameters.PAYLOAD_KEY_SAMPLE_RATE] = DefaultParameters.SAMPLE_RATE_16K

    def set_enable_intermediate_result(self, data):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_INTERMEDIATE_RESULT] = data

    def set_enable_punctuation_prediction(self, data):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_PUNCTUATION_PREDICTION] = data

    def set_enable_inverse_text_normalization(self, data):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_ITN] = data

    def set_user_id(self,data):
        self._payload[Parameters.PAYLOAD_KEY_USER_ID] = data


    def set_customization_id(self, data):
        self._payload[Parameters.PAYLOAD_KEY_CUSTOMIZATION_ID] = data

    def set_audio_url(self, data):
        self._payload['audio_url'] = data

    def set_vocabulary_id(self, data):
        self._payload[Parameters.PAYLOAD_KEY_VOCABULARY_ID] = data

    def set_enable_save_log(self, flag=False):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_SAVE_LOG] = flag

    def set_max_sentence_silence(self, max_sentence_silence):
        self._payload[Parameters.PAYLOAD_KEY_MAX_SENTENCE_SILENCE] = max_sentence_silence

    def set_speaker_id(self, data, **kwargs):
        if kwargs:
            kwargs[Parameters.PAYLOAD_KEY_SPEAKER_ID] = data
            self._payload = kwargs
        else:
            self._payload[Parameters.PAYLOAD_KEY_SPEAKER_ID] = data

    def get_speaker_id(self):
        self._header[Parameters.HEADER_KEY_NAME] = Parameters.HEADER_VALUE_SPEAKER_START
        return {Parameters.HEADER: self._header, Parameters.PAYLOAD: self._payload}

    def set_mandatory_clause(self, data):
        if data:
            self._header[Parameters.HEADER_KEY_NAMESPACE] = Parameters.HEADER_VALUE_TRANS_NAMESPACE
            self._header[Parameters.HEADER_KEY_NAME] = Parameters.HEADER_VALUE_TRANS_NAME_SENTENCE_END
        else:
            pass

    def get_mandatory_clause(self, ):
        return self._header

    def start(self):
        """
        Start to identify and create a new connection to the server
        """

    def send(self, data, is_BINARY=True):

        """
        Send voice data to the server. It is recommended to send 1000-8000 bytes each time
        :param data: Binary audio data
        :return: Send successfully, return 0
                 Send failed, return - 1
        """
        if self._status == Parameters.STATUS_STARTED:
            if is_BINARY:
                self._ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
            else:
                self._ws.send(data, opcode=websocket.ABNF.OPCODE_TEXT)
            return 0
        else:
            _log.error('should not send data in state %d', self._status)
            return -1

    def close(self):
        """
        Close websocket
        """
        if self._ws:
            if self._thread and self._thread.is_alive():
                self._ws.keep_running = False
                self._thread.join()
            self._ws.close()

    def stop(self):
        """
        End identification and close the connection with the server
        """
