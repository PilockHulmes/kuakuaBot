from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

import aiofiles

__plugin_meta__ = PluginMetadata(
    name="alconna_send_voiceline",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (
    Args,
    Field,
    Voice,
    Option,
    Arparma,
    Alconna,
    on_alconna,
)

speak_test = on_alconna(
    Alconna(
        "测试说话",
        Args[("character", str)]
    ),
    use_cmd_start=True,
    auto_send_output=True,
    skip_for_unmatch=True,
    priority=15,
)

def get_wav_duration(wav_bytes: bytes) -> float:
    audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
    return len(audio) / 1000

@speak_test.handle()
async def handleSpeakTest(arp: Arparma):
    character:str = arp.main_args["character"]
    if character == "符玄":
        async with aiofiles.path("~/Downloads/sony2.wav", "rb") as f:
            wav_bytes = await f.read()
        duration = get_wav_duration(wav_bytes)
        mimetype = "audio/wav"
        await speak_test.finish(Voice(raw=wav_bytes, mimetype=mimetype, duration=duration))
    speak_test.finish()