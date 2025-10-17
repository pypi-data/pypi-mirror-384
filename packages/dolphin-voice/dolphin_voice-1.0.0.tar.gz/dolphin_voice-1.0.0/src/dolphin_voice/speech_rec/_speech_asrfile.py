# -*- coding: utf-8 -*-

import time
import json
import traceback
import requests
from dolphin_voice.speech_rec._log import _log
from dolphin_voice.speech_rec.parameters import Parameters


class SpeechASRFile():

    def __init__(self, asr_file_upload_url=None, asr_file_result_url=None):
        
        if asr_file_upload_url:
            self.asr_file_upload_url = asr_file_upload_url
        else:
            self.asr_file_upload_url = 'https://api.voice.dolphin-ai.jp/v1/asrfile/upload'
        
        if asr_file_result_url:
            self.asr_file_result_url = asr_file_result_url
        else:
            self.asr_file_result_url = 'https://api.voice.dolphin-ai.jp/v1/asrfile/result'
    
    def transcribe_file(self, files, data, token):
        try:
            url = self.asr_file_upload_url
            header={Parameters.HEADER_KEY_Authorization: "Bearer {}".format(token)}

            retry_count = 1
            while retry_count:
                try:
                    response = requests.post(url=url, files=files, data=data, headers=header)
                    break
                except:
                    retry_count -= 1
                    traceback.print_exc()
                    time.sleep(1)
            _log.debug(f'response: {response.content}')
            res = response.json()
            _log.debug(f'res: {res}')

            task_id = res['data']['task_id']
            get_task_id_url = f"{self.asr_file_result_url}?task_id={task_id}"
            
            chongshi = True
            while chongshi:
                # 获取结果
                try:
                    res = requests.get(get_task_id_url).json()
                except:
                    traceback.print_exc()
                    time.sleep(1)
                    continue

                _log.debug(f'res: {res}')

                if 'desc' in res['data'] and res['data']['desc'] == 'Failed':
                    _log.info(f'{res}')
                    return {}
                if 'statistics' in res['data'] and 'finish_time' in res['data']['statistics'] and res['data']['statistics']['finish_time']:
                    return res
                else:
                    time.sleep(1)

            return {}
        except:
            traceback.print_exc()
            return {}

