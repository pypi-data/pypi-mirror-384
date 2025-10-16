import io
import random

import aiohttp
import numpy as np


async def async_search_custom_music(data) -> tuple[dict, bool]:
    search_url = f"https://music-api.gdstudio.xyz/api.php?types=search&name={data['music_name']}&count=100&pages=1"

    # 为搜索请求设置 10 秒超时
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(search_url) as response:
            response_json = await response.json()

    music_list = []
    first_music_list = []
    other_music_list1 = []
    other_music_list2 = []
    for line in response_json:
        if data.get("author_name") and data["author_name"] in line["artist"][0]:
            first_music_list.append(line)
        elif data.get("author_name") and (data["author_name"] in line["artist"] or data["author_name"] in line["name"]):
            other_music_list1.append(line)
        else:
            other_music_list2.append(line)

    if len(first_music_list) <= 10:
        music_list = first_music_list
        random.shuffle(other_music_list2)
        music_list = music_list + other_music_list1[: 20 - len(music_list)]
        music_list = music_list + other_music_list2[: 20 - len(music_list)]

    # print(data)
    # print("找到音乐，数量：", len(first_music_list), len(music_list))

    if not music_list:
        return {}, False
    return {"message": "已找到歌曲", "music_list": music_list}, False


async def _get_random_music_info(id_list: list) -> dict:
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        random.shuffle(id_list)

        for music_id in id_list:
            url = f"https://music-api.gdstudio.xyz/api.php?types=url&id={music_id}&br=128"
            async with session.get(url) as response:
                res_json = await response.json()
            if res_json.get("url"):
                break

    return res_json


async def async_mcp_play_music(data) -> tuple[list, bool]:
    try:
        from pydub import AudioSegment
    except ImportError:
        return [], True

    id_list = data["id_list"]
    res_json = await _get_random_music_info(id_list)

    if not res_json:
        return [], False

    pcm_list = []
    buffer = io.BytesIO()
    # 为下载音乐文件设置 60 秒超时（音乐文件可能比较大）
    download_timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=download_timeout) as session:
        async with session.get(res_json["url"]) as resp:
            async for chunk in resp.content.iter_chunked(1024):
                buffer.write(chunk)

    buffer.seek(0)
    audio = AudioSegment.from_mp3(buffer)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 2 bytes = 16 bits
    pcm_data = audio.raw_data

    chunk_size = 960 * 2
    for i in range(0, len(pcm_data), chunk_size):
        chunk = pcm_data[i : i + chunk_size]

        if chunk:  # 确保不添加空块
            chunk = np.frombuffer(chunk, dtype=np.int16)
            pcm_list.extend(chunk)

    return pcm_list, False
