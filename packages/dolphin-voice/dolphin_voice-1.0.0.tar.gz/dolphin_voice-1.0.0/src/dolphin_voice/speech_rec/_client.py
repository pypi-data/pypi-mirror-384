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
from dolphin_voice.speech_rec._log import _log
from dolphin_voice.speech_rec._token import Token
from dolphin_voice.speech_rec._speech_recognizer import SpeechRecognizer
from dolphin_voice.speech_rec._speech_transcriber import SpeechTranscriber
from dolphin_voice.speech_rec._utils import utils
from dolphin_voice.speech_rec._speech_asrfile import SpeechASRFile
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
        cipher_suite = Fernet(self.context)
        self.donation = cipher_suite.decrypt(self.donation).decode()


    @staticmethod
    def set_log_level(level):
        _log.setLevel(level)

    def get_token(self, app_id, app_secret, token_file):
        token = Token.get_token(app_id, app_secret, PRO_ENVIRONMENT=self._pro_environment)
        with open(token_file, "w", encoding="utf-8") as fd:
            fd.write(str({"token": token[0], "time": time.time()}))
        return Token.get_token(app_id, app_secret)

    def create_recognizer(self, callback, url=None):
        if url:
            request = SpeechRecognizer(callback, url)
        else:
            request = SpeechRecognizer(callback, self.donation)
        return request

    def create_transcriber(self, callback, url=None):
        if url:
            transcriber = SpeechTranscriber(callback, url)
        else:
            transcriber = SpeechTranscriber(callback, self.donation)
        return transcriber

    def create_asrfile(self, asr_file_upload_url=None, asr_file_result_url=None):
        asrfile = SpeechASRFile(asr_file_upload_url=asr_file_upload_url, asr_file_result_url=asr_file_result_url)
        return asrfile
