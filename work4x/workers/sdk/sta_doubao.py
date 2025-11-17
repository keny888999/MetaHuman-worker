import time
import os
import requests
from tts_doubao import appID, accessKey

appid = appID
base_url = f'https://openspeech.bytedance.com/api/v1/vc'
access_token = 'wMdMBAj-jIQ5cdllekEdJOeUeQFd0yBE'
file_url = "http://oss.work4x.com/work4x/audio/20251110/1666_1762757262175.mp3"
audio_text = """
您知道吗？我这双手啊，能同时玩转五种乐器。三分钟解决一个数学难题，五秒钟记住一百个电话号码。朋友都说我脑袋里装着永不停歇的马达，连睡觉都在构思新点子。不过最绝的是——我还能边喝咖啡边用脚趾头写代码，这本事您说神不神？
"""


def log_time(func):
    def wrapper(*args, **kw):
        begin_time = time.time()
        func(*args, **kw)
        print('total cost time = {time}'.format(time=time.time() - begin_time))
    return wrapper


def format_timestamp(milliseconds):
    """将毫秒数格式化为SRT时间戳"""
    # 转换为小时、分钟、秒和毫秒
    hours = int(milliseconds // 3600000)
    milliseconds %= 3600000

    minutes = int(milliseconds // 60000)
    milliseconds %= 60000

    seconds = int(milliseconds // 1000)
    milliseconds = int(milliseconds % 1000)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def segments_to_srt(segments, output_file):
    """将优化后的片段转换为SRT格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            # 确保时间戳是数值类型
            start_ms = float(segment['start_time'])
            end_ms = float(segment['end_time'])

            start_time = format_timestamp(start_ms)
            end_time = format_timestamp(end_ms)

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment['text']}\n\n")

# 辅助函数：秒转毫秒（如果原始数据是秒为单位）


def seconds_to_milliseconds(segments):
    """将秒为单位的时间戳转换为毫秒"""
    for segment in segments:
        segment['start'] = segment['start'] * 1000
        segment['end'] = segment['end'] * 1000
    return segments


@log_time
def audio_to_srt(file_url: str, audio_text: str):
    response = requests.post(
        '{base_url}/submit'.format(base_url=base_url),
        params=dict(
            appid=appid,
            caption_type='speech',
            language='zh-CN'
        ),
        json={
            # 'audio_text': audio_text,
            'url': file_url,
        },
        headers={
            'Authorization': 'Bearer; {}'.format(access_token)
        }
    )
    assert (response.status_code == 200)

    print('submit response = {}'.format(response.text))
    assert (response.status_code == 200)
    assert (response.json()['message'] == 'Success')

    job_id = response.json()['id']
    response = requests.get(
        '{base_url}/query'.format(base_url=base_url),
        params=dict(
            appid=appid,
            id=job_id,
        ),
        headers={
            'Authorization': 'Bearer; {}'.format(access_token)
        }
    )
    assert (response.status_code == 200)

    data = response.json()
    segments = data["utterances"]
    save_path = os.path.join(os.path.dirname(__file__), 'srt.txt')
    segments_to_srt(segments, save_path)
    print("success!")


if __name__ == '__main__':
    audio_to_srt(file_url, audio_text)
