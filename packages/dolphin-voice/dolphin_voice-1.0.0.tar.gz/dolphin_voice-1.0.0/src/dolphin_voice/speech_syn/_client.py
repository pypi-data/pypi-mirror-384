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
import time
import websocket
from cryptography.fernet import Fernet

try:
    import thread
except ImportError:
    import _thread as thread
from dolphin_voice.speech_syn._log import _log
from dolphin_voice.speech_syn._token import Token
from dolphin_voice.speech_syn._speech_synthesizer import SpeechSynthesizer
from dolphin_voice.speech_syn._utils import utils
__all__ = ["SpeechClient"]


class SpeechClient(utils):
    context = "PRzgbfEoV85LyiLHln4kSnthacgmlZnqMfYKyN7jmxI="

    def __init__(self, pro_environment=True):
        super().__init__()
        websocket.enableTrace(False)
        self._pro_environment = pro_environment
        if self._pro_environment:
            self.donation = b'gAAAAABmkJOgN3O7BbCmfZoQjLKDlJRp251ojQ2Npiap_bLaM6MRD0Rao6QTmQsyQCFhAGX4nnQN_n0k2s3VjfoR3VxvFfNlCKLPjnc7Zw4CgPc4HFjU5nuhvjzhAiX8v-Fn-fk5_mWS'
        else:
            self.donation = b'gAAAAABmkJOgN3O7BbCmfZoQjLKDlJRp251ojQ2Npiap_bLaM6MRD0Rao6QTmQsyQCFhAGX4nnQN_n0k2s3VjfoR3VxvFfNlCKLPjnc7Zw4CgPc4HFjU5nuhvjzhAiX8v-Fn-fk5_mWS'
        self.donation = "wss://api.voice.dolphin-ai.jp/v1/tts/ws"

    @staticmethod
    def set_log_level(level):
        _log.setLevel(level)

    def get_token(self, app_id, app_secret, token_file):
        token = Token.get_token(app_id, app_secret, PRO_ENVIRONMENT=self._pro_environment)
        with open(token_file, "w", encoding="utf-8") as fd:
            fd.write(str({"token": token[0], "time": time.time()}))
        return Token.get_token(app_id, app_secret)
    
    def create_synthesizer(self, callback, url=None):
        if url:
            synthesizer = SpeechSynthesizer(callback, url)
        else:
            synthesizer = SpeechSynthesizer(callback, self.donation)
        return synthesizer
    
