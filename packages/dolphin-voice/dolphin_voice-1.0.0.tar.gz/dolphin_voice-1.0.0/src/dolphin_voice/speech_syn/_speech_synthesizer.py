# -*- coding: utf-8 -*-

"""
 * *
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
import six
import websocket
import uuid
import threading
import time

from dolphin_voice.speech_syn._log import _log
from dolphin_voice.speech_syn.parameters import Parameters
from dolphin_voice.speech_syn._speech_control import SpeechControl


class SpeechSynthesizer(SpeechControl):
    def __init__(self, callback, url):
        super(SpeechSynthesizer, self).__init__(callback, url)

        self._header[Parameters.HEADER_KEY_NAMESPACE] = Parameters.HEADER_VALUE_TTS_NAMESPACE
    def start(self, ping_interval=5, ping_timeout=3, retry_count=3):
        """
        Start to identify and create a new connection to the server
        :param retry_count: Try to connect retry_count times
        :param ping_interval: Automatically send ping command, specify the sending interval, in seconds
        :param ping_timeout: Timeout in seconds for waiting to receive a Pong message
        :return: Successfully established connection with server, return 0
                 Failed to establish connection with server, return - 1
        """
        if self._status == Parameters.STATUS_INIT:
            _log.debug('starting synthesizer...')
            self._status = Parameters.STATUS_STARTING
        else:
            _log.error("Illegal status: %s" % self._status)
            return -1

        def _open(ws):
            _log.debug('websocket connected')
            self._status = Parameters.STATUS_STARTED
            self._is_connected = True
            time.sleep(0.04)
            msg_id = six.u(uuid.uuid1().hex)
            self._task_id = six.u(uuid.uuid1().hex)
            self._header[Parameters.HEADER_KEY_NAME] = Parameters.HEADER_VALUE_TTS_NAME_START
            self._header[Parameters.HEADER_KEY_MESSAGE_ID] = msg_id
            self._header[Parameters.HEADER_KEY_TASK_ID] = self._task_id
            text = self.serialize()
            _log.info('sending start cmd: ' + text)
            ws.send(text)

        def _data(ws, raw, opcode, flag):
            if opcode == websocket.ABNF.OPCODE_BINARY:
                _log.debug("received binary data, size: %s" % len(raw))
                self._callback.binary_data_received(raw)
            elif opcode == websocket.ABNF.OPCODE_TEXT:
                _log.debug("websocket message received: %s" % raw)
                msg = json.loads(raw)
                name = msg[Parameters.HEADER][Parameters.HEADER_KEY_NAME]
                if name == Parameters.HEADER_VALUE_TTS_NAME_COMPLETED:
                    self._status = Parameters.STATUS_STOPPED
                    _log.debug('websocket status changed to stopped')
                    _log.debug('callback on_completed')
                    self._callback.completed(msg)
                    self._ws.close()
                elif name == Parameters.HEADER_VALUE_TTS_NAME_STARTED:
                    self._status = Parameters.STATUS_STARTED
                    _log.debug('websocket status changed to started')
                    _log.debug('callback on_started')
                    self._callback.started(msg)
                elif name == Parameters.HEADER_VALUE_TTS_NAME_TIMESTAMP: 
                    self._status = Parameters.STATUS_STOPPED
                    self._callback.get_Timestamp(msg)
                elif name == Parameters.HEADER_VALUE_TTS_NAME_DURATION:
                    self._status = Parameters.STATUS_STOPPED
                    self._callback.get_Duration(msg)
                elif name == Parameters.HEADER_VALUE_NAME_TASK_FAILED:
                    self._status = Parameters.STATUS_STOPPED
                    _log.error(msg)
                    _log.debug('websocket status changed to stopped')
                    _log.debug('callback on_task_failed')
                    self._callback.task_failed(msg)
                elif name ==Parameters.HEADER_VALUE_NAME_TASK_FAILED_WARING:
                    _log.error(msg)
                    _log.debug('websocket status changed to stopped')
                    _log.debug('callback on_task_failed')

        def _close(ws,a,b):
            _log.debug('callback on_channel_closed',a,b)
            self._callback.channel_closed()

        def _error(ws, error):
            if self._connected or self._last_start_retry:
                _log.error(error)
                self._status = Parameters.STATUS_STOPPED
                message = json.loads('{"header":{"namespace":"Default","name":"TaskFailed",'
                                     '"status":400,"message_id":"0","task_id":"0",'
                                     '"status_text":"%s"}}'
                                     % error)
                self._callback.task_failed(message)
            else:
                _log.warning('retry start: %s' % error)

        for count in range(retry_count):
            self._status = Parameters.STATUS_STARTING
            if count == (retry_count - 1):
                self._last_start_retry = True

            # Init WebSocket
            self._ws = websocket.WebSocketApp(self._url,
                                              on_open=_open,
                                              on_data=_data,
                                              on_error=_error,
                                              on_close=_close,
                                              header={Parameters.HEADER_KEY_Authorization: "Bearer {}".format(self.get_token()),
                                                      Parameters.HEADER_KEY_APPID: self.get_app_id(),
                                                      Parameters.HEADER_SDK_VALUE_NAME_LANG: Parameters.HEADER_SDK_VALUE_NAME})

            self._thread = threading.Thread(target=self._ws.run_forever, args=(None, None, ping_interval, ping_timeout))
            self._thread.daemon = True
            self._thread.start()
            # waite for no more than 10 seconds
            for i in range(1000):
                if self._status == Parameters.STATUS_STARTED or self._status == Parameters.STATUS_STOPPED:
                    break
                else:
                    time.sleep(0.01)

            if self._status == Parameters.STATUS_STARTED:
                # Successfully established the connection with the server
                _log.debug('start succeed!')
                return 0
            else:
                if self._connected or self._last_start_retry:
                    # If the websocket link has been established but the connection with the server fails,
                    # or the last retry, a - 1 will be returned
                    _log.error("start failed, status: %s" % self._status)
                    return -1
                else:
                    # Try to reconnect
                    continue

    def wait_completed(self):
        """
        Wait for synthesis to finish
        :return: End of composition, return 0
                 Synthesis timeout, return - 1
        """
        ret = 0
        if self._status == Parameters.STATUS_STARTED:
            for i in range(100):
                if self._status == Parameters.STATUS_STOPPED:
                    break
                else:
                    time.sleep(0.04)
                    _log.debug('waite 40ms')

            if self._status != Parameters.STATUS_STOPPED:
                ret = -1
            else:
                ret = 0
        else:
            _log.error('should not wait completed in state %d', self._status)
            ret = -1
        return ret
