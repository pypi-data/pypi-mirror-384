import asyncio
import os
import sys
import time

import numpy as np
import sounddevice as sd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from xiaozhi_sdk import XiaoZhiWebsocket
from xiaozhi_sdk.utils import read_audio_file

sample_rate = 48000
frame_duration = 60
MAC_ADDR = "00:22:44:66:88:00"


async def assistant_audio_play(audio_queue, wait_time=5):
    # 创建一个持续播放的流
    stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype=np.int16)
    stream.start()
    last_time = int(time.time())
    while True:
        if not audio_queue:
            await asyncio.sleep(0.01)
            if last_time and time.time() - last_time > wait_time:
                break

            continue

        pcm_data = audio_queue.popleft()

        # 将字节数据转换为 numpy int16 数组
        audio_array = pcm_data

        stream.write(audio_array)
        last_time = time.time()

    stream.stop()
    stream.close()


async def message_handler_callback(message):
    print("message received:", message)
    if message["type"] == "music":
        print("music:", message["text"])


async def test_main():
    xiaozhi = XiaoZhiWebsocket(message_handler_callback, audio_sample_rate=sample_rate,
                               audio_frame_duration=frame_duration)

    await xiaozhi.init_connection(MAC_ADDR)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_audio_file = "../file/audio/test_16k.wav"

    if sample_rate == 24000:
        test_audio_file = "../file/audio/test_24k.wav"
    elif sample_rate == 48000:
        test_audio_file = "../file/audio/test_48k.wav"
    wav_path = os.path.join(current_dir, test_audio_file)

    for pcm in read_audio_file(wav_path, sample_rate, frame_duration):
        await xiaozhi.send_audio(pcm)
    await xiaozhi.send_silence_audio()

    await assistant_audio_play(xiaozhi.output_audio_queue)

    for pcm in read_audio_file(wav_path, sample_rate, frame_duration):
        await xiaozhi.send_audio(pcm)
    await xiaozhi.send_silence_audio()

    await assistant_audio_play(xiaozhi.output_audio_queue)

    for pcm in read_audio_file(wav_path, sample_rate, frame_duration):
        await xiaozhi.send_audio(pcm)
    await xiaozhi.send_silence_audio()

    await assistant_audio_play(xiaozhi.output_audio_queue)

    time.sleep(10)

    await xiaozhi.close()


if __name__ == "__main__":
    asyncio.run(test_main())
