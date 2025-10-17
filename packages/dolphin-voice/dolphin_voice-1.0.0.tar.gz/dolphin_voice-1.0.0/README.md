

## Installation

Install the Dolphin Voice Python SDK using pip:

```bash
pip install dolphin_voice
```

## Usage

### Quick Start

#### Short Speech Recognition

```python
# -*- coding: utf-8 -*-
import os
import time
import threading
from dolphin_voice import speech_rec
from dolphin_voice.speech_rec.callbacks import SpeechRecognizerCallback
from dolphin_voice.speech_rec.parameters import DefaultParameters

token = None
expire_time = 7  # Expiration time


class Callback(SpeechRecognizerCallback):
    """
    The parameters of the constructor are not required. You can add them as needed
    The name parameter in the example can be used as the audio file name to be recognized for distinguishing in multithreading
    """

    def __init__(self, name='SpeechRecognizer'):
        self._name = name

    def started(self, message):
        print('MyCallback.OnRecognitionStarted: %s' % message)

    def result_changed(self, message):
        print('MyCallback.OnRecognitionResultChanged: file: %s, task_id: %s, payload: %s' % (
            self._name, message['header']['task_id'], message['payload']))

    def completed(self, message):
        print('MyCallback.OnRecognitionCompleted: file: %s, task_id:%s, payload:%s' % (
            self._name, message['header']['task_id'], message['payload']))

    def task_failed(self, message):
        print(message)

    def warning_info(self, message):
        print(message)

    def channel_closed(self):
        print('MyCallback.OnRecognitionChannelClosed')

def solution(client, app_id, app_secret, audio_path, lang_type, kwargs):
    """
    Recognize speech,single thread
    :param client: SpeechClient
    :param app_id: Your app_id
    :param app_secret: Your app_secret
    :param audio_path: Audio path
    :param lang_type: Language type
    """
    assert os.path.exists(audio_path), "Audio file path error, please check your audio path."
    sample_rate = kwargs.get("sample_rate", DefaultParameters.SAMPLE_RATE_16K)
    each_audio_format = kwargs.get("audio_format", DefaultParameters.WAV)
    field_ = kwargs.get("field", DefaultParameters.FIELD)

    if judging_expire_time(app_id, app_secret, expire_time):
        callback = Callback(audio_path)
        recognizer = client.create_recognizer(callback)
        recognizer.set_app_id(app_id)
        recognizer.set_token(token)
        # fixme You can customize the configuration according to the official website documentation
        payload = {
            "lang_type": lang_type,
            "format": each_audio_format,
            "field": field_,
            "sample_rate": sample_rate,
        }
        recognizer._payload.update(**payload)
        try:
            ret = recognizer.start()
            if ret < 0:
                return ret
            print('sending audio...')
            cnt = 0
            with open(audio_path, 'rb') as f:
                audio = f.read(7680)
                while audio:
                    cnt += 0.24
                    ret = recognizer.send(audio)
                    if ret < 0:
                        break
                    time.sleep(0.24)
                    audio = f.read(7680)
            recognizer.stop()
        except Exception as ee:
            print(f"send ee:{ee}")
        finally:
            recognizer.close()
    else:
        print("token expired")


def judging_expire_time(app_id, app_secret, extime):
    global token
    new_time = time.time()
    token_file = "SpeechRecognizer_token.txt"
    if not os.path.exists(token_file):
        client.get_token(app_id, app_secret, token_file)
    with open(token_file, "r", encoding="utf-8") as fr:
        token_info = eval(fr.read())
    old_time = token_info['time']
    token = token_info['token']
    flag = True
    if new_time - old_time > 60 * 60 * 24 * (extime - 1):
        flag, _ = client.get_token(app_id, app_secret, token_file)
        if flag:
            flag = True
            pass
        else:
            for i in range(7):
                flag, _ = client.get_token(app_id, app_secret, token_file)
                if flag is not None:
                    flag = True
                    break
    return flag


def channels_split_solution(audio_path, right_path, left_path, **kwargs):
    client = kwargs.get('client')
    appid = kwargs.get('app_id')
    appsecret = kwargs.get('app_secret')
    langtype = kwargs.get('lang_type')
    remove_audio = kwargs.get('rm_audio', True)
    client.auto_split_audio(audio_path, right_path, left_path)
    thread_list = []
    thread_r = threading.Thread(target=solution, args=(client, appid, appsecret, right_path, langtype, kwargs))
    thread_list.append(thread_r)
    thread_l = threading.Thread(target=solution, args=(client, appid, appsecret, left_path, langtype, kwargs))
    thread_list.append(thread_l)
    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()
    if remove_audio:
        os.remove(right_path)
        os.remove(left_path)
    pass


if __name__ == "__main__":
    client = speech_rec.SpeechClient()
    # Set the level of output log information：DEBUG、INFO、WARNING、ERROR
    client.set_log_level('INFO')
    # Type your app_id and app_secret
    app_id = ""  # your app id
    app_secret = ""  # your app secret
    audio_path = "demo.mp3"  # audio path
    lang_type = "zh-cmn-Hans-CN"  # lang type
    field = ""  # field
    sample_rate = 16000  # sample rate [int] 16000 or 8000
    audio_format = "mp3"  # audio format
    channel = 1
    assert app_id and app_secret and audio_path and lang_type and sample_rate and audio_format, "Please check args"
    
    if sample_rate == 8000:
        field = 'call-center'
    
    # fixme This is just a simple example, please modify it according to your needs.
    if channel == 1:
        kwargs = {
            "field": field,
            "sample_rate": sample_rate,
            "audio_format":audio_format
        }
        solution(client, app_id, app_secret, audio_path, lang_type, kwargs)

    elif channel == 2 and sample_rate == 8000:
        # Dual channel 8K audio solution
        channels_split_solution(audio_path=audio_path,
                                left_path=f"left.{audio_format}",
                                right_path=f"right.{audio_format}",
                                client=client,
                                app_id=app_id,
                                app_secret=app_secret,
                                lang_type=lang_type,
                                field=field,
                                sample_rate=sample_rate,
                                audio_format=audio_format)
    else:
        print('channel error')

```

#### Real-time Speech Recognition

```python
# -*- coding: utf-8 -*-
import json
import os.path
import time
import threading
import traceback

from dolphin_voice import speech_rec
from dolphin_voice.speech_rec.callbacks import SpeechTranscriberCallback
from dolphin_voice.speech_rec.parameters import DefaultParameters, Parameters

token = None
expire_time = 7  # Expiration time

info_list = [[], [], False]


class MyCallback(SpeechTranscriberCallback):
    """
    The parameters of the constructor are not required. You can add them as needed
    The name parameter in the example can be used as the audio file name to be recognized for distinguishing in multithreading
    """

    def __init__(self, name='default'):
        self._name = name

    def started(self, message):
        self.print_message(message)

    def result_changed(self, message):
        self.print_message(message)

    def sentence_begin(self, message):
        self.print_message(message)

    def sentence_end(self, message):
        global info_list
        channel = message['header']['user_id']
        begin_time = message['payload']['begin_time']
        end_time = message['payload']['time']
        result = message['payload']['result']
        if channel == "left" or channel == "right":
            if channel == "left":
                if result:
                    info_list[0].append([channel, begin_time, end_time, result])
            elif channel == "right":
                if result:
                    info_list[1].append([channel, begin_time, end_time, result])
            self.print_info()
        else:
            print(message)

    def completed(self, message):
        try:
            print(message)
        except Exception as ee:
            print(ee)
            traceback.print_exc()
        global info_list
        info_list[2] = True

    def print_info(self, ):
        left_list = info_list[0]
        right_list = info_list[1]
        if_end = info_list[2]

        def format_string(data_list, list_name):
            channel, begin_time, end_time, result = data_list[0]
            if list_name == "left_list":
                info_list[0].pop(0)
            else:
                info_list[1].pop(0)

            return f"channel:{channel}\tbegin_time:{begin_time}\tend_time:{end_time}\tresult:{result}"

        if left_list and right_list:
            while True:
                if not left_list and not right_list:
                    break
                if left_list and right_list:
                    left_begin_time = left_list[0][1]
                    left_end_time = left_list[0][2]
                    right_begin_time = right_list[0][1]
                    right_end_time = right_list[0][2]
                    if left_begin_time == right_begin_time and left_end_time > right_end_time:
                        print(format_string(right_list, "right_list"))
                    elif left_begin_time == right_begin_time and left_end_time <= right_end_time:
                        print(format_string(left_list, "left_list"))
                    elif left_begin_time < right_begin_time:
                        print(format_string(left_list, "left_list"))
                    elif left_begin_time >= right_begin_time:
                        print(format_string(right_list, "right_list"))
                if left_list and not right_list:
                    if left_end_time > right_end_time:
                        break
                    else:
                        print(format_string(left_list, "left_list"))
                if not left_list and right_list:
                    if right_end_time > left_end_time:
                        print(format_string(right_list, "right_list"))
                    else:
                        break
        elif if_end:
            while left_list:
                print(format_string(left_list, "left_list"))
            while right_list:
                print(format_string(right_list, "right_list"))

    def print_message(self, message):
        channel = message['header']['user_id']
        if channel == "left" or channel == "right":
            pass
        else:
            print(message)

    def task_failed(self, message):
        print(message)

    def warning_info(self, message):
        print(message)

    def channel_closed(self):
        print('MyCallback.OnTranslationChannelClosed')


def solution(client, app_id, app_secret, audio_path, lang_type, kwargs):
    """
    Transcribe speech,single thread
    :param client: SpeechClient
    :param app_id: Your app_id
    :param app_secret: Your app_secret
    :param audio_path: Audio path
    :param lang_type: Language type
    """
    each_audio_format = kwargs.get("audio_format", DefaultParameters.MP3)
    field_ = kwargs.get("field", DefaultParameters.FIELD)
    user_id = kwargs.get("user_id", "default")
    assert os.path.exists(audio_path), "Audio file path error, please check your audio path."
    if judging_expire_time(app_id, app_secret, expire_time):
        callback = MyCallback(audio_path)
        transcriber = client.create_transcriber(callback)
        transcriber.set_app_id(app_id)
        transcriber.set_token(token)
        # fixme You can customize the configuration according to the official website documentation
        payload = {
            "lang_type": lang_type,
            "format": each_audio_format,
            "field": field_,
            "sample_rate": sample_rate,
            "user_id": user_id
        }
        transcriber._payload.update(**payload)
        try:
            ret = transcriber.start()
            if ret < 0:
                return ret
            with open(audio_path, 'rb') as f:
                audio = f.read(7680)
                cnt = 0
                while audio:
                    ret = transcriber.send(audio)
                    # fixme: If you need to mandatory clause or set speaker id by yourself, please use the codes below

                    # Default, customizable and changeable
                    # if cnt % 768000 == 0:
                    #     # Mandatory clause setting
                    #     transcriber.set_mandatory_clause(True)
                    #     transcriber._header = transcriber.get_mandatory_clause()
                    #     transcriber.send(json.dumps({Parameters.HEADER: transcriber._header}), False)
                    #     # Set speaker ID
                    #     transcriber.set_speaker_id(speaker_id)
                    #     speaker_id_info = transcriber.get_speaker_id()
                    #     transcriber.send(json.dumps(speaker_id_info), False)
                    #     print("Mandatory and Set speaker:",transcriber._payload)

                    if ret < 0:
                        break
                    cnt += 7680
                    time.sleep(0.24)
                    audio = f.read(7680)
            transcriber.stop()
        except Exception as e:
            print(e)
        finally:
            transcriber.close()
    else:
        print("token expired")


def judging_expire_time(app_id, app_secret, extime):
    global token
    token_file = "SpeechTranscriber_token.txt"
    new_time = time.time()
    if not os.path.exists(token_file):
        client.get_token(app_id, app_secret, token_file)

    with open(token_file, "r", encoding="utf-8") as fr:
        token_info = eval(fr.read())
    old_time = token_info['time']
    token = token_info['token']
    flag = True
    if new_time - old_time > 60 * 60 * 24 * (extime - 1):
        flag, _ = client.get_token(app_id, app_secret, token_file)
        if flag:
            flag = True
            pass
        else:
            for i in range(7):
                flag, _ = client.get_token(app_id, app_secret, token_file)
                if flag is not None:
                    flag = True
                    break
    return flag


def channels_split_solution(audio_path, right_path, left_path, **kwargs):
    client = kwargs.get('client')
    appid = kwargs.get('app_id')
    appsecret = kwargs.get('app_secret')
    langtype = kwargs.get('lang_type')
    remove_audio = kwargs.get('rm_audio', True)
    client.auto_split_audio(audio_path, right_path, left_path)
    thread_list = []
    right_kwargs = kwargs.copy()
    right_kwargs["user_id"] = "right"
    thread_r = threading.Thread(target=solution, args=(client, appid, appsecret, right_path, langtype, right_kwargs))
    thread_list.append(thread_r)
    left_kwargs = kwargs.copy()
    left_kwargs["user_id"] = "left"
    thread_l = threading.Thread(target=solution, args=(client, appid, appsecret, left_path, langtype, left_kwargs))
    thread_list.append(thread_l)
    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()
    if remove_audio:
        try:
            os.remove(right_path)
            os.remove(left_path)
        except Exception as ee:
            print(ee)
            traceback.print_exc()


if __name__ == "__main__":
    client = speech_rec.SpeechClient()
    # Set the level of output log information：DEBUG、INFO、WARNING、ERROR
    client.set_log_level('INFO')
    # Type your app_id and app_secret
    app_id = ""  # your app id
    app_secret = ""  # your app secret
    audio_path = "demo.mp3"  # audio path
    lang_type = "zh-cmn-Hans-CN"  # lang type
    field = ""  # field
    sample_rate = 16000  # sample rate [int] 16000 or 8000
    audio_format = "mp3"  # audio format
    channel = 1
    assert app_id and app_secret and audio_path and lang_type and sample_rate and audio_format, "Please check args"
    
    if sample_rate == 8000:
        field = 'call-center'

    #fixme This is just a simple example, please modify it according to your needs.
    if channel == 1:
        kwargs = {
            "field": field,
            "sample_rate": sample_rate,
            "audio_format": audio_format,
            "user_id": "",
        }
        solution(client, app_id, app_secret, audio_path, lang_type, kwargs)
    elif channel == 2 and sample_rate == 8000:
        # Dual channel 8K audio solution
        channels_split_solution(audio_path=audio_path,
                                left_path=f"left.{audio_format}",
                                right_path=f"right.{audio_format}",
                                client=client,
                                app_id=app_id,
                                app_secret=app_secret,
                                lang_type=lang_type,
                                field=field,
                                sample_rate=sample_rate,
                                audio_format=audio_format,
                                )
    else:
        print('channel error')
```

#### Audio File Transcription

```python
# -*- coding: utf-8 -*-
import os
import time
import threading
from dolphin_voice import speech_rec
from dolphin_voice.speech_rec.callbacks import SpeechRecognizerCallback
from dolphin_voice.speech_rec.parameters import DefaultParameters

token = None
expire_time = 7  # Expiration time



def judging_expire_time(app_id, app_secret, extime):
    global token
    new_time = time.time()
    token_file = "SpeechASRFile_token.txt"
    if not os.path.exists(token_file):
        client.get_token(app_id, app_secret, token_file)
    with open(token_file, "r", encoding="utf-8") as fr:
        token_info = eval(fr.read())
    old_time = token_info['time']
    token = token_info['token']
    flag = True
    if new_time - old_time > 60 * 60 * 24 * (extime - 1):
        flag, _ = client.get_token(app_id, app_secret, token_file)
        if flag:
            flag = True
            pass
        else:
            for i in range(7):
                flag, _ = client.get_token(app_id, app_secret, token_file)
                if flag is not None:
                    flag = True
                    break
    return flag

if __name__ == "__main__":
    client = speech_rec.SpeechClient()
    # Set the level of output log information：DEBUG、INFO、WARNING、ERROR
    client.set_log_level('DEBUG')
    # Type your app_id and app_secret
    app_id = ""  # your app id
    app_secret = ""  # your app secret
    assert app_id and app_secret

    audio = "demo.mp3"

    if judging_expire_time(app_id, app_secret, expire_time):
        asrfile = client.create_asrfile()    
        files=[('file',(f'{audio}',open(audio,'rb'),'audio/wav'))]
        data = {
            "lang_type": "zh-cmn-Hans-CN",
            "format": "mp3",
            "sample_rate": 16000
        }
        result = asrfile.transcribe_file(files, data, token)
        print(result)
```

#### Text-to-Speech

```python
# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import wave
from dolphin_voice import speech_syn

from dolphin_voice.speech_syn.callbacks import SpeechSynthesizerCallback
from dolphin_voice.speech_syn.parameters import DefaultParameters

token = None
expire_time = 7


class MyCallback(SpeechSynthesizerCallback):
    def __init__(self, name):
        self._name = name
        self._fout = open(name, 'wb')

    def binary_data_received(self, raw):
        self._fout.write(raw)

    def started(self, message):
        print('MyCallback.OnSynthseizerStarted: %s' % message)

    def get_Timestamp(self,message):
        print('MyCallback.OnSynthseizerGetTimestamp: %s' % message)

    def get_Duration(self, message):
        print('MyCallback.OnSynthseizerGetDuration: %s' % message)

    def result_changed(self, message):
        print('MyCallback.OnSynthseizerChanged: %s' % message)

    def completed(self, message):
        print('MyCallback.OnSynthseizerCompleted: %s' % message)
        self._fout.close()

    def task_failed(self, message):
        print('MyCallback.OnSynthseizerTaskFailed-task_id:%s, status_text:%s' % (
            message['header']['task_id'], message['header']['status_text']))
        self._fout.close()

    def channel_closed(self):
        print('MyCallback.OnSynthseizerChannelClosed')

def safe_int(value, default):
    try:
        return float(value) if value else default
    except ValueError:
        print(f"Warning: Invalid integer value '{value}', using default '{default}'")
        return default


def solution(client, app_id, app_secret, text, audio_name, lang_type, format, 
             sampe_rate, voice, volume, speech_rate, pitch_ratio, emotion, silence_duration,
             enable_timestamp):
    """
    Synthesize speech,single thread
    :param client: SpeechClient
    :param app_id: Your app_id
    :param app_secret: Your app_secret
    :param text: Text to be synthesized
    :param audio_name: File save path
    :param lang_type: language type
    """
    global expire_time
    if judging_expire_time(app_id, app_secret, expire_time):
        callback = MyCallback(audio_name)
        synthesizer = client.create_synthesizer(callback)
        synthesizer.set_app_id(app_id)
        synthesizer.set_token(token)
        synthesizer.set_lang_type(lang_type)
        synthesizer.set_text(text)
        synthesizer.set_voice(voice or DefaultParameters.voice)
        synthesizer.set_format(format or DefaultParameters.PCM)
        synthesizer.set_sample_rate(safe_int(sampe_rate, DefaultParameters.SAMPLE_RATE_24K))
        synthesizer.set_volume(safe_int(volume, DefaultParameters.volume_ratio))
        synthesizer.set_speech_rate(safe_int(speech_rate, DefaultParameters.speech_rate))
        synthesizer.set_pitch_rate(safe_int(pitch_ratio, DefaultParameters.pitch_ratio))
        synthesizer.set_emotion(emotion or DefaultParameters.emotion)
        synthesizer.set_silence_duration(safe_int(silence_duration, DefaultParameters.silence_duration))
        synthesizer.set_enable_timestamp(enable_timestamp or DefaultParameters.enable_timestamp)
        # synthesizer.set_enable_english_opt(enable_english_opt or DefaultParameters.enable_english_opt)


        try:
            ret = synthesizer.start()
            if ret < 0:
                return ret
            synthesizer.wait_completed()
        except Exception as e:
            print(e)
        finally:
            synthesizer.close()
    else:
        print("token expired")

def judging_expire_time(app_id, app_secret, extime):
    global token
    token_file = "tts_token.txt"
    new_time = time.time()
    if not os.path.exists(token_file):
        client.get_token(app_id, app_secret, token_file)
    with open(token_file, "r", encoding="utf-8") as fr:
        token_info = eval(fr.read())
    old_time = token_info['time']
    token = token_info['token']
    flag = True
    if new_time - old_time > 60 * 60 * 24 * (extime - 1):
        flag, _ = client.get_token(app_id, app_secret, token_file)
        if flag:
            flag = True
            pass
        else:
            for i in range(7):
                flag, _ = client.get_token(app_id, app_secret, token_file)
                if flag is not None:
                    flag = True
                    break
    return flag


def pcm_to_wav(pcm_path, wav_path, channels=1, sample_rate=16000, sample_width=2):
    """将 PCM 文件转换为 WAV 文件"""
    with open(pcm_path, 'rb') as pcmfile:
        pcm_data = pcmfile.read()

    with wave.open(wav_path, 'wb') as wavfile:
        wavfile.setnchannels(channels)       # 声道数（1=单声道，2=双声道）
        wavfile.setsampwidth(sample_width)   # 采样字节宽度（2=16bit）
        wavfile.setframerate(sample_rate)    # 采样率（Hz）
        wavfile.writeframes(pcm_data)


if __name__ == "__main__":
    client = speech_syn.SpeechClient()
    # Set the level of output log information: debug, info, warning, error
    client.set_log_level('INFO')
    # Type your app_id and app_secret
    app_id = ""  # your app id
    app_secret = ""  # your app secret
    assert app_id and app_secret
    # Type your text and lang_type
    text = "今天是个晴天，您吃过了吗？"
    # Optional: zh-cmn-Hans-CN en-US ja-JP
    lang_type = 'zh-cmn-Hans-CN'

    # Optional: Set the parameters of the synthesis
    format = ''                        # Default: pcm, Optional: mp3, 
    voice = ''                          # Default: Xiaohui 
    sampe_rate = ''                     # Default: 24K, Optional: 16K, 8k
    volume = ''                         # Default: 1.0, Optional: 0.1-3.0
    speech_rate = ''                    # Default: 1.0, Optional: 0.2-3.0
    pitch_ratio = ''                    # Default: 1.0, Optional: 0.1-3.0
    emotion = ''                        # Default: None
    silence_duration = ''               # Default：125
    enable_timestamp = False               # Default: False
    audio_name = f'syAudio.pcm'
    solution(client, app_id, app_secret, text, audio_name, lang_type, format, 
             sampe_rate, voice, volume, speech_rate, pitch_ratio, emotion, silence_duration,
             enable_timestamp)

    if format == 'pcm' or not format:
        pcm_to_wav(audio_name, audio_name.replace('.pcm', '.wav'), sample_rate=safe_int(sampe_rate, DefaultParameters.SAMPLE_RATE_24K))


```