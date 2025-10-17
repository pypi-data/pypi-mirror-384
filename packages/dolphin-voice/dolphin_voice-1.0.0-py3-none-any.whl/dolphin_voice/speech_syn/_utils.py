#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import subprocess
import traceback
import wave


class utils(object):
    @staticmethod
    def auto_split_audio(audio_path, right_path, left_path, **kwargs):
        os.system(
            f"ffmpeg -i {audio_path} -map_channel 0.0.0 {left_path} -map_channel 0.0.1 {right_path} -y -loglevel quiet")

    def get_audio_info(self, audio_path):
        if not audio_path.endswith(".wav"):
            temp_audio_path = "temp_audio.wav"
            res = os.system(f"ffmpeg -i {audio_path} {temp_audio_path} -y -loglevel quiet")
            if res != 0:
                raise ValueError("The audio is damaged!")
            audio_path = temp_audio_path
        with wave.open(audio_path, "rb") as f:
            n_channels, sample_width, framerate, n_frames, comptype, compname = f.getparams()
        try:
            os.remove("temp_audio.wav")
        except:
            pass
        return {
            'channel': n_channels,
            'sample_width': sample_width,
            'framerate': framerate,
            'frames': n_frames,
            'comptype': comptype,
            'compname': compname
        }

    def audio2mp3(self,file_path: str, sampleRate=16000):
        """
        Convert audio format
        It will overwrite the file with the same name, please operate with caution.
        @param file_path: Audio file path.
        @return:
        """
        t = file_path.rsplit(".", 1)[0] + ".mp3"
        cmd = f"ffmpeg -i {file_path} -ac 1 -ar {sampleRate} -sample_fmt s16 -codec:a libmp3lame -b:a 128k {t} -y -loglevel quiet"
        try:
            flag = subprocess.run(cmd, shell=True)
            if flag.returncode == 0:
                return True, f"{t}"
            else:
                exit("Please check if ffmpeg is installed and configured correctly!")
        except Exception as ee:
            print(ee)
            return False, None