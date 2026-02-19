# -*- coding: utf-8 -*-
# @Project : tob_service
# @Company : ByteDance
# @Time    : 2025/7/10 19:01
# @Author  : SiNian
# @FileName: TTSv3HttpDemo.py
# @IDE: PyCharm
# @Motto：  I,with no mountain to rely on,am the mountain myself.
import requests
import json
import base64
import os

# python版本：==3.11

# -------------客户需要填写的参数----------------
appID = "4129319043"
accessKey = "wMdMBAj-jIQ5cdllekEdJOeUeQFd0yBE"
resourceID = "seed-tts-1.0"
# ---------------请求地址----------------------
url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"


def tts_http_stream(text: str, settings: dict):
    session = requests.Session()
    headers = {
        "X-Api-App-Id": appID,
        "X-Api-Access-Key": accessKey,
        "X-Api-Resource-Id": resourceID,
        "X-Api-App-Key": "aGjiRDfUWi",
        "Content-Type": "application/json",
        "Connection": "keep-alive"
    }

    params = {
        "user": {
            "uid": "123123"
        },
        "req_params": {
            "text": text,
            "speaker": settings.get('character'),
            "audio_params": {
                "format": "mp3",
                "sample_rate": 32 * 1000,
                "speech_rate": settings.get('speed', 0),
                "emotion": settings.get('emotion', ""),
                "emotion_scale": 5,
                "enable_timestamp": True,
                "loudness_rate": settings.get('volume', 0),
            },
            "additions": "{\"disable_markdown_filter\":false, \"enable_timestamp\":true}\"}"
        }
    }

    sentences = []

    try:
        print('请求的params:\n', params)
        response = session.post(url, headers=headers, json=params, stream=True)

        # 用于存储音频数据
        audio_data = bytearray()
        sentences = []
        total_audio_size = 0
        for chunk in response.iter_lines(decode_unicode=True):
            if not chunk:
                continue
            data = json.loads(chunk)

            if data.get("code", 0) == 0 and "data" in data and data["data"]:
                chunk_audio = base64.b64decode(data["data"])
                audio_size = len(chunk_audio)
                total_audio_size += audio_size
                audio_data.extend(chunk_audio)
                continue
            if data.get("code", 0) == 0 and "sentence" in data and data["sentence"]:
                # print("sentence_data:", data)
                sentences.append(data["sentence"])
                continue
            if data.get("code", 0) == 20000000:
                break
            if data.get("code", 0) > 0:
                raise Exception(f"error response:{data}")

        if len(audio_data) < 1:
            raise Exception(f"generate failed: audio_data is empty")

        # with open("./sentence.json", "w", encoding="utf-8") as f:
        #    f.write(json.dumps(sentences, ensure_ascii=False))

        return audio_data, sentences

    finally:
        response.close()
        session.close()


if __name__ == "__main__":
    # ---------------请求地址----------------------

    payload = {
        "user": {
            "uid": "123123"
        },
        "req_params": {
            "text": "你好",
            "speaker": "zh_male_yuzhouzixuan_moon_bigtts",
            "audio_params": {
                "format": "mp3",
                "sample_rate": 24000,
                "enable_timestamp": True
            },
            "additions": "{\"explicit_language\":\"zh\",\"disable_markdown_filter\":true, \"enable_timestamp\":true}\"}"
        }
    }

    # tts_http_stream(url=url, params=payload, audio_save_path="tts_test.mp3")
