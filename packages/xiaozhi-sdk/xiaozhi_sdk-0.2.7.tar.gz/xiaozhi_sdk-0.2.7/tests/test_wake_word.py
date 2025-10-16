import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from xiaozhi_sdk import XiaoZhiWebsocket
from xiaozhi_sdk.utils import read_audio_file

sample_rate = 16000
frame_duration = 60

MAC_ADDR = "00:22:44:66:88:00"

URL = None
ota_url = None


async def test_main():
    is_end = asyncio.Event()
    async def message_handler_callback(message):
        if message.get("state") == "stop":
            is_end.set()
        print("message received:", message)

    xiaozhi = XiaoZhiWebsocket(
        message_handler_callback, url=URL, ota_url=ota_url,
        audio_sample_rate=sample_rate, audio_frame_duration=frame_duration)
    await xiaozhi.init_connection(MAC_ADDR)

    await xiaozhi.send_wake_word("你好")
    await asyncio.sleep(5)

    # await xiaozhi.send_wake_word("1+1")
    # await asyncio.sleep(5)
    #
    # await xiaozhi.send_wake_word("你是什么大语言模型")
    # await asyncio.sleep(5)

    # say hellow
    for pcm in read_audio_file("./file/audio/16k_say_hello.wav", sample_rate, frame_duration):
        await xiaozhi.send_audio(pcm)
    await xiaozhi.send_silence_audio()
    await asyncio.sleep(5)

    await xiaozhi.close()


if __name__ == "__main__":
    asyncio.run(test_main())



