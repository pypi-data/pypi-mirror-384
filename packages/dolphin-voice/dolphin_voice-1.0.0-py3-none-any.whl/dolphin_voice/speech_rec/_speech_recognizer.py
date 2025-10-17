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
import ssl
import platform

import six
import websocket
import uuid
import threading
import time
from dolphin_voice.speech_rec._log import _log
from dolphin_voice.speech_rec.parameters import Parameters
from dolphin_voice.speech_rec._speech_control import SpeechControl


class SpeechRecognizer(SpeechControl):

    def __init__(self, callback, url):
        super(SpeechRecognizer, self).__init__(callback, url)
        self._header[Parameters.HEADER_KEY_NAMESPACE] = Parameters.HEADER_VALUE_ASR_NAMESPACE

    def start(self, ping_interval=3, ping_timeout=2, retry_count=5):
        """
        Start to identify and create a new connection to the server
        :param retry_count: Try to connect retry_count times
        :param ping_interval: Automatically send ping command, specify the sending interval, in seconds
        :param ping_timeout: Timeout in seconds for waiting to receive a Pong message
        :return: Successfully established connection with server, return 0
                 Failed to establish connection with server, return - 1
        """
        if self._status == Parameters.STATUS_INIT:
            _log.debug('starting recognizer...')
            self._status = Parameters.STATUS_STARTING
        else:
            _log.error("Illegal status: %s" % self._status)
            return -1

        # Parameters required to connect to websocket
        def _open(ws):
            _log.debug('websocket connected')
            self._status = Parameters.STATUS_CONNECTED
            self._is_connected = True
            msg_id = six.u(uuid.uuid1().hex)
            self._task_id = six.u(uuid.uuid1().hex)
            self._header[Parameters.HEADER_KEY_NAME] = Parameters.HEADER_VALUE_ASR_NAME_START
            self._header[Parameters.HEADER_KEY_MESSAGE_ID] = msg_id
            self._header[Parameters.HEADER_KEY_TASK_ID] = self._task_id
            send_text = self.serialize()
            _log.info('sending start cmd: ' + send_text)
            ws.send(send_text)

        def _message(ws, res):
            _log.debug('websocket message received: ' + res)
            res = json.loads(res)
            data = res[Parameters.HEADER][Parameters.HEADER_KEY_NAME]
            if data == 'Warning':
                warning_info = \
                    f"Warning\t{Parameters.HEADER_KEY_TASK_ID}:{res[Parameters.HEADER][Parameters.HEADER_KEY_TASK_ID]}\t" \
                    f"{Parameters.HEADER_KEY_STATUS}:{res[Parameters.HEADER][Parameters.HEADER_KEY_STATUS]}\t" \
                    f"{Parameters.HEADER_KEY_STATUS_TEXT}:{res[Parameters.HEADER][Parameters.HEADER_KEY_STATUS_TEXT]}"
                _log.warning(res)
                warning_info = f"\033[33m{warning_info}\033[0m"
                self._callback.warning_info(warning_info)
            elif data == 'Error':
                error_msg = f"Error\t{Parameters.HEADER_KEY_TASK_ID}:{res[Parameters.HEADER][Parameters.HEADER_KEY_TASK_ID]}\t" \
                            f"{Parameters.HEADER_KEY_STATUS}:{res[Parameters.HEADER][Parameters.HEADER_KEY_STATUS]}\t" \
                            f"{Parameters.HEADER_KEY_STATUS_TEXT}:{res[Parameters.HEADER][Parameters.HEADER_KEY_STATUS_TEXT]}"
                self._callback.task_failed(f"\033[31m{error_msg}\033[0m")
                _log.error(error_msg)
                exit()
            elif data == Parameters.HEADER_VALUE_ASR_NAME_STARTED:
                self._status = Parameters.STATUS_STARTED
                _log.debug('callback started')
                self._callback.started(res)
            elif data == Parameters.HEADER_VALUE_ASR_NAME_RESULT_CHANGED:
                _log.debug('callback result_changed')
                self._callback.result_changed(res)
            elif data == Parameters.HEADER_VALUE_ASR_NAME_COMPLETED:
                if self._status == Parameters.STATUS_STOPPING:
                    # The completed event returned from the client's active call to stop
                    self._status = Parameters.STATUS_STOPPED
                else:
                    # Enable VAD and the completed event returned by the server
                    self._status = Parameters.STATUS_COMPLETED
                _log.debug('websocket status changed to stopped')
                _log.debug('callback completed')
                self._callback.completed(res)
                self._ws.close()
            elif data == Parameters.HEADER_VALUE_NAME_TASK_FAILED:
                self._status = Parameters.STATUS_STOPPED
                _log.error(res)
                _log.debug('websocket status changed to stopped')
                _log.debug('callback task_failed')
                self._callback.task_failed(res)
                exit()

        def _error(ws, error):
            if self._connected or self._last_start_retry:
                _log.error(error)
                self._status = Parameters.STATUS_STOPPED
                message = json.loads('{"header":{"namespace":"Default","name":"TaskFailed",'
                                     '"status":400,"message_id":"0","task_id":"0",'
                                     '"status_text":"%s"}}'
                                     % error)
                if eval(str(error)) is not None:
                    self._callback.task_failed(f"\033[31m{message}\033[0m")
                exit()
            else:
                _log.warning('retry start: %s' % error)

        def _close(ws):
            _log.debug('callback channel_closed')
            self._callback.channel_closed()

        for count in range(retry_count):
            self._status = Parameters.STATUS_STARTING
            if count == (retry_count - 1):
                self._last_start_retry = True

            # Init WebSocket
            self._ws = websocket.WebSocketApp(self._url,
                                              on_open=_open,
                                              on_message=_message,
                                              on_error=_error,
                                              on_close=_close,
                                              header={Parameters.HEADER_KEY_Authorization: "Bearer {}".format(self.get_token()),
                                                      Parameters.CONTEXT_SDK_KEY_VERSION: Parameters.CONTEXT_SDK_VALUE_VERSION,
                                                      Parameters.CONTEXT_SDK_KEY_OS: platform.system(),
                                                      Parameters.CONTEXT_SDK_KEY: Parameters.CONTEXT_SDK_VALUE_NAME_LANG,
                                                      })
            # Init Thread
            self._thread = threading.Thread(target=self._ws.run_forever,
                                            # {"cert_reqs": ssl.CERT_NONE}
                                            # None, None, ping_interval, ping_timeout
                                            args=(None, None, None, None))
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
                print("Successfully established the connection with the server")
                _log.debug('start succeed!')
                return 0
            else:
                if self._connected or self._last_start_retry:
                    # If the websocket link has been established but the connection with the server fails,
                    # or the last retry, a - 1 will be returned
                    print("Websocket link established but failed to connect with server")
                    _log.error("start failed, status: %s" % self._status)
                    return -1
                else:
                    # Try to reconnect
                    print("Try to reconnect")
                    continue

    def stop(self):
        """
        End identification and close the connection with the server
        :return: Closed successfully, return 0
                 Closed failed, return - 1
        """
        ret = 0
        if self._status == Parameters.STATUS_COMPLETED:
            ret = 0
        elif self._status == Parameters.STATUS_STARTED:
            self._status = Parameters.STATUS_STOPPING
            msg_id = six.u(uuid.uuid1().hex)
            self._header[Parameters.HEADER_KEY_NAME] = Parameters.HEADER_VALUE_ASR_NAME_STOP
            self._header[Parameters.HEADER_KEY_MESSAGE_ID] = msg_id
            self._payload.clear()
            send_text = self.serialize()
            _log.info('sending stop cmd: ' + send_text)
            self._ws.send(send_text)
            while True:
                if self._status == Parameters.STATUS_STOPPED:
                    break
                else:
                    time.sleep(0.1)
                    _log.debug('waite 100ms')
            if self._status != Parameters.STATUS_STOPPED:
                ret = -1
            else:
                ret = 0
        else:
            _log.error('should not stop in state %d', self._status)
            ret = -1
        return ret


