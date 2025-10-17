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
from dolphin_voice.speech_syn._log import _log
from dolphin_voice.speech_syn.parameters import Parameters
from dolphin_voice.speech_syn._speech import Speech
from dolphin_voice.speech_syn.parameters import DefaultParameters


class SpeechControl(Speech):

    def __init__(self, callback, url):
        super(SpeechControl, self).__init__(callback, url)

        self._last_start_retry = False
        self._connected = False

        self._header[Parameters.HEADER_KEY_NAMESPACE] = None

        self._payload[Parameters.PAYLOAD_KEY_FORMAT] = DefaultParameters.MP3
        self._payload[Parameters.PAYLOAD_KEY_SAMPLE_RATE] = DefaultParameters.SAMPLE_RATE_24K

    def set_text(self, text):
        self._payload[Parameters.PAYLOAD_KEY_TEXT] = text

    def set_voice(self, voice):
        self._payload[Parameters.PAYLOAD_KEY_VOICE] = voice

    def set_volume(self, volume):
        self._payload[Parameters.PAYLOAD_KEY_VOLUME] = volume

    def set_speech_rate(self, speech_rate):
        self._payload[Parameters.PAYLOAD_KEY_SPEECH_RATE] = speech_rate

    def set_pitch_rate(self, pitch_rate):
        self._payload[Parameters.PAYLOAD_KEY_PITCH_RATE] = pitch_rate

    def set_enable_timestamp(self, enable_timestamp):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_TIMESTAMP] = enable_timestamp

    def set_emotion(self, emotion):
        self._payload[Parameters.PAYLOAD_KEY_EMOTION] = emotion

    def set_enable_english_opt(self, enable_english_opt):
        self._payload[Parameters.PAYLOAD_KEY_ENABLE_ENGLISH_OPT] = enable_english_opt
    
    def set_silence_duration(self, silence_duration):
        self._payload[Parameters.PAYLOAD_KEY_SILENCE_DURATION] = silence_duration

        

    def start(self):
        """
        Start to identify and create a new connection to the server
        """

    def wait_completed(self):
        """
        Wait for synthesis to finish
        :return: End of composition, return 0
                 Synthesis timeout, return - 1
        """

    def close(self):
        """
        Close websocket
        """
        if self._ws:
            if self._thread and self._thread.is_alive():
                self._ws.keep_running = False
                self._thread.join()
            self._ws.close()