# coding=utf-8
import sys
from dashscope.audio.tts import SpeechSynthesizer
# 若没有将API Key配置到环境变量中，需将apiKey替换为自己的API Key

import dashscope
dashscope.api_key = "sk-8d6fadb22aeb4d03b23e403909a781f8"

result = SpeechSynthesizer.call(model='sambert-zhihao-v1',
                                text='从事作战相关职业的军人必须按照男性标准进行体能测试，成绩需达到70%的评分或以上。在外表仪容上，赫格塞思宣布不再允许留胡须，并批评发胖的士兵和将领',
                                sample_rate=16000,
                                format='mp3')
if result.get_audio_data() is not None:
    with open('output.mp3', 'wb') as f:
        f.write(result.get_audio_data())
    print('SUCCESS: get audio data: %d bytes in output' % (sys.getsizeof(result.get_audio_data())))
else:
    print('ERROR: response is %s' % (result.get_response()))
