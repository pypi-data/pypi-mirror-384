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
    CONTEXT_SDK_VALUE_VERSION = '1.0.0.6'

    # head
    HEADER = 'header'
    HEADER_KEY_NAMESPACE = 'namespace'
    HEADER_KEY_NAME = 'name'
    HEADER_KEY_MESSAGE_ID = 'message_id'
    HEADER_KEY_TASK_ID = 'task_id'
    HEADER_KEY_STATUS = 'status'
    HEADER_KEY_STATUS_TEXT = 'status_text'
    HEADER_KEY_Authorization = 'Authorization'
    HEADER_PING = 'ping'
    HEADER_PONG = 'pong'

    # payload
    PAYLOAD = 'payload'
    PAYLOAD_KEY_SAMPLE_RATE = 'sample_rate'
    PAYLOAD_KEY_FORMAT = 'format'
    PAYLOAD_KEY_ENABLE_ITN = 'enable_inverse_text_normalization'
    PAYLOAD_KEY_ENABLE_INTERMEDIATE_RESULT = 'enable_intermediate_result'
    PAYLOAD_KEY_ENABLE_PUNCTUATION_PREDICTION = 'enable_punctuation_prediction'
    PAYLOAD_KEY_ENABLE_WORDS = 'enable_words'
    PAYLOAD_KEY_LANG_TYPE = 'lang_type'
    PAYLOAD_KEY_CUSTOMIZATION_ID = 'customization_id'
    PAYLOAD_KEY_VOCABULARY_ID = 'vocabulary_id'
    PAYLOAD_KEY_MAX_SENTENCE_SILENCE = 'max_sentence_silence'
    PAYLOAD_KEY_SPEAKER_ID = 'speaker_id'
    PAYLOAD_KEY_FIELD = 'field'
    PAYLOAD_KEY_ENABLE_SAVE_LOG = "enable_save_log"
    PAYLOAD_KEY_USER_ID = "user_id"

    # speech recognizer
    HEADER_VALUE_ASR_NAMESPACE = 'SpeechRecognizer'
    HEADER_VALUE_ASR_NAME_START = 'StartRecognition'
    HEADER_VALUE_ASR_NAME_STOP = 'StopRecognition'
    HEADER_VALUE_ASR_NAME_STARTED = 'RecognitionStarted'
    HEADER_VALUE_ASR_NAME_RESULT_CHANGED = 'RecognitionResultChanged'
    HEADER_VALUE_ASR_NAME_COMPLETED = 'RecognitionCompleted'
    HEADER_VALUE_NAME_TASK_FAILED = 'TaskFailed'

    # speech transcriber
    HEADER_VALUE_TRANS_NAMESPACE = 'SpeechTranscriber'
    HEADER_VALUE_TRANS_NAME_START = 'StartTranscription'
    HEADER_VALUE_TRANS_NAME_STOP = 'StopTranscription'
    HEADER_VALUE_TRANS_NAME_STARTED = 'TranscriptionStarted'
    HEADER_VALUE_TRANS_NAME_SENTENCE_BEGIN = 'SentenceBegin'
    HEADER_VALUE_TRANS_NAME_SENTENCE_END = 'SentenceEnd'
    HEADER_VALUE_TRANS_NAME_RESULT_CHANGE = 'TranscriptionResultChanged'
    HEADER_VALUE_TRANS_NAME_COMPLETED = 'TranscriptionCompleted'
    HEADER_VALUE_SPEAKER_START = 'SpeakerStart'

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
    PAYLOAD_KEY_AUDIO_URL = 'audio_url'


class DefaultParameters:
    # Format
    FIELD = 'general'
    FIELD_8k = 'call-center'
    MP3 = 'mp3'
    WAV = 'wav'
    # SampleRate
    SAMPLE_RATE_16K = 16000
    SAMPLE_RATE_8K = 8000
