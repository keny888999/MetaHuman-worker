import requests

api_url = "https://api.minimaxi.com/v1/t2a_v2"
api_key = "sk-api-ibJIFzC-tcU2vgDoaY8Xc1uxQRw34vihx7VCDu7fLwe-3cwFBxxBxI9SuthESeaGDtCaRGFQElhfL9YYj2TImSCTz87PXEVdIPjgoY05z6pSpCZysmR49bE"


def tts(text: str, params: dict, save_path: str):
    url = api_url
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "speech-2.6-hd",
        "text": text,
        "stream": False,
        "output_format": "url",
        "voice_setting": {
            "voice_id": params.get("character", "male-qn-qingse"),
            "speed": params.get("speed", 0) * 0.01 + 1,  # 豆包[-50,100] 到 [0.5,2.0] 的线性映射
            "vol": 0, #params.get("volume", 0),  # 豆包[-50,100] 到 [0,10] 的线性映射
            "pitch": params.get("pitch", 0),  # 豆包也是[-12,12] 无需映射
            "emotion": params.get("emotion")  # 支持 happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1
        },
        "pronunciation_dict": {
            "tone": [
                "处理/(chu3)(li3)",
                "危险/dangerous"
            ]
        },
        "subtitle_enable": False
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    res = response.json()
    print("*" * 30)
    print(res)
    print("*" * 30)

    data = res.get("data")
    if not data:
        raise Exception("data 为空")

    audio_url = data.get("audio")
    if not audio_url:
        raise Exception("audio 为空")

    response = requests.get(audio_url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return True


if __name__ == "__main__":
    save_path = "./minmax-test.mp3"
    tts("Não tínhamos combinado de nos encontrar na escola amanhã de manhã bem cedo? Por que você mudou de planos de novo?", save_path)
    print("成功调用")
