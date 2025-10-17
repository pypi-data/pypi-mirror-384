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


class SpeechRecognizerCallback:
    """
    * @brief Call start (), successfully establish a connection with the service, the SDK internal thread reports the started event.
    * @note  Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def started(self, message):
        raise Exception('Not implemented!')

    """
    * @brief Set the parameters that allow the return of intermediate results. 
    *        When SDK receives the service and returns the intermediate results, 
    *        the SDK internal thread reports the ResultChanged event.
    * @note  Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def result_changed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief SDK receives a Completed event when it receives the end of identification message returned by the service
    * @note  After reporting the Completed event, the SDK will close the internal identification channel. 
    *        Calling send () at this time will return -1, please stop sending.
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def completed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief When an exception occurs during the identification process .
    *        (including start (), send (), stop ()), the SDK internal thread reports a TaskFailed event.
    * @note  After reporting the TaskFailed event, the SDK will close the internal identification channel. 
    *        Calling send () at this time will return -1, please stop sending.
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def task_failed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief When the recognition is ended or an exception occurs, the websocket connection channel will be closed.
    * @note  Do not call stop () operation inside the callback function.
    * @return
    """

    def channel_closed(self):
        raise Exception('Not implemented!')

    """
    * @brief This is the method of printing warning messages.
    * @note  Do not call stop () operation inside the callback function.
    * @return
    """

    def warning_info(self,message):
        raise Exception('Not implemented!')


class SpeechTranscriberCallback:
    """
    * @brief Call start (), successfully establish a connection with the service,
    *        the SDK internal thread reports the started event.
    * @note  Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def started(self, message):
        raise Exception('Not implemented!')

    """
    * @brief Set the parameters that allow the return of intermediate results. 
    *        When SDK receives the service and returns the intermediate results, 
    *        the SDK internal thread reports the ResultChanged event.
    * @note  Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def result_changed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief The SDK recognizes the beginning of a sentence after receiving the service return, 
    *        and the SDK internal thread reports the SentenceBegin event.
    * @note  This event is the start of detecting a sentence. 
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def sentence_begin(self, message):
        raise Exception('Not implemented!')

    """
    * @brief The SDK recognizes the beginning of a sentence after receiving the service return, 
    *        and the SDK internal thread reports the SentenceBegin event.
    * @note  This event is the start of detecting a sentence. 
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def sentence_end(self, message):
        raise Exception('Not implemented!')

    """
    * @brief SDK receives a Completed event when it receives the end of identification message returned by the service.
    * @note  After reporting the Completed event, the SDK will close the internal identification channel. 
    *        Calling send () at this time will return -1, please stop sending.
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def completed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief When an exception occurs during the identification process.
    *        (including start (), send (), stop ()), the SDK internal thread reports a TaskFailed event.
    * @note  After reporting the TaskFailed event, the SDK will close the internal identification channel. 
    *        Calling send () at this time will return -1, please stop sending.
    *        Do not call stop () operation inside the callback function.
    * @param message The response returned by the service.
    * @return
    """

    def task_failed(self, message):
        raise Exception('Not implemented!')

    """
    * @brief When the recognition is ended or an exception occurs, the websocket connection channel will be closed.
    * @note  Do not call stop () operation inside the callback function.
    * @return
    """

    def channel_closed(self):
        raise Exception('Not implemented!')


    """
    * @brief This is the method of printing warning messages.
    * @note  Do not call stop () operation inside the callback function.
    * @return
    """

    def warning_info(self,message):
        raise Exception('Not implemented!')
