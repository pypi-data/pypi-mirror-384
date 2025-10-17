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


class Parameters:
    # Initial state
    STATUS_INIT = 1
    # websocket connected，_open
    STATUS_CONNECTED = 2
    # Connecting with service
    STATUS_STARTING = 3
    # Connection with service established successfully，_message RecognitionStarted
    STATUS_STARTED = 4
    # The client is actively disconnecting
    STATUS_STOPPING = 5
    # Disconnected from service
    STATUS_STOPPED = 6
    # Open VAD, the service actively returns the completed event
    STATUS_COMPLETED = 7

    # context
    CONTEXT = 'context'
    CONTEXT_SDK_KEY = 'sdk'
    CONTEXT_SDK_KEY_NAME = 'name'
    CONTEXT_SDK_KEY_OS = 'os'
    CONTEXT_SDK_VALUE_NAME = 'speech-sdk-python'
    CONTEXT_SDK_VALUE_NAME_LANG = 'python'
    CONTEXT_SDK_KEY_VERSION = 'version'
    CONTEXT_SDK_VALUE_VERSION = '1.0.0.0'

    # head
    HEADER = 'header'
    HEADER_KEY_NAMESPACE = 'namespace'
    HEADER_KEY_NAME = 'name'
    HEADER_SDK_VALUE_NAME_LANG = 'sdk'
    HEADER_SDK_VALUE_NAME = 'python'
    HEADER_KEY_MESSAGE_ID = 'message_id'
    HEADER_KEY_TASK_ID = 'task_id'
    HEADER_KEY_STATUS = 'status'
    HEADER_KEY_STATUS_TEXT = 'status_text'
    HEADER_KEY_Authorization = 'Authorization'
    HEADER_PING = 'ping'
    HEADER_PONG = 'pong'
    HEADER_KEY_APPID = 'X-AppID'

    # payload
    PAYLOAD = 'payload'
    PAYLOAD_KEY_SAMPLE_RATE = 'sample_rate'
    PAYLOAD_KEY_FORMAT = 'format'
    PAYLOAD_KEY_ENABLE_ITN = 'enable_inverse_text_normalization'
    PAYLOAD_KEY_ENABLE_INTERMEDIATE_RESULT = 'enable_intermediate_result'
    PAYLOAD_KEY_ENABLE_PUNCTUATION_PREDICTION = 'enable_punctuation_prediction'
    PAYLOAD_KEY_LANG_TYPE = 'lang_type'

    # speech synthesizer
    PAYLOAD_KEY_VOICE = 'voice'
    PAYLOAD_KEY_TEXT = 'text'
    PAYLOAD_KEY_VOLUME = 'volume'
    PAYLOAD_KEY_COMPESSION_RATE = 'compression_rate'
    PAYLOAD_KEY_SPEECH_RATE = 'speech_rate'
    PAYLOAD_KEY_PITCH_RATE = 'pitch_rate'
    PAYLOAD_KEY_ENABLE_TIMESTAMP = 'enable_timestamp'
    PAYLOAD_KEY_EMOTION = 'emotion'
    PAYLOAD_KEY_ENABLE_ENGLISH_OPT = 'enable_english_opt'
    PAYLOAD_KEY_SILENCE_DURATION = 'silence_duration'
 

    HEADER_VALUE_NAME_TASK_FAILED = 'Error'
    HEADER_VALUE_NAME_TASK_FAILED_WARING = 'Warning'

    # speech synthesizer
    HEADER_VALUE_TTS_NAMESPACE = 'SpeechSynthesizer'
    HEADER_VALUE_TTS_NAME_START = 'StartSynthesis'
    HEADER_VALUE_TTS_NAME_STARTED = 'SynthesisStarted'
    HEADER_VALUE_TTS_NAME_TIMESTAMP = 'SynthesisTimestamp'
    HEADER_VALUE_TTS_NAME_DURATION = 'SynthesisDuration'
    HEADER_VALUE_TTS_NAME_COMPLETED = 'SynthesisCompleted'
    

    # token
    TOKEN_APP_ID = 'app_id'
    TOKEN_TIMESTAMP = 'timestamp'
    TOKEN_SIGNATURE_NONCE = 'signatureNonce'
    TOKEN_SIGNATURE = 'signature'
    TOKEN_STATUS = 'status'
    TOKEN_DATA = 'data'
    TOKEN_APP_TOKEN = 'token'
    TOKEN_EXPIRE_TIME = 'expireTime'
    TOKEN_MESSAGE = 'message'
    

class DefaultParameters:
    # Format
    PCM = 'pcm'
    WAV = 'wav'
    MP3 = 'mp3'
    OGG_OPUS = 'ogg_opus'

    # SampleRate
    SAMPLE_RATE_8K = 8000
    SAMPLE_RATE_16K = 16000
    SAMPLE_RATE_24K = 24000

    # voice
    voice = "Xiaohui"

    compression_rate = 1
    speech_rate	= 1
    volume_ratio = 1
    pitch_ratio = 1
    enable_timestamp = False
    enable_english_opt = False

    emotion = ''
    silence_duration = 125

