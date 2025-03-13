from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule
from .config import Config
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
import aiofiles
from pydub import AudioSegment
import io
import httpx

__plugin_meta__ = PluginMetadata(
    name="alconna_send_voiceline",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

from nonebot import require
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


whiltelist = [
    1020882307,
    853041949,
    244960293,
]
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in whiltelist

speak_test = on_alconna(
    Alconna(
        "测试说话",
        Args["character", str].add(name="text", value=str, default="").add(name="lang", value=str, default="zh"),
    ),
    use_cmd_start=True,
    auto_send_output=True,
    skip_for_unmatch=True,
    priority=10,
    rule=Rule(group_in_whitelist)
)

def get_wav_duration(wav_bytes: bytes) -> float:
    audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
    return len(audio) / 1000

@speak_test.handle()
async def handleSpeakTest(arp: Arparma):
    character:str = arp.main_args["character"]
    text: str = arp.main_args["text"]
    text = text.removeprefix("\"").removesuffix("\"")
    lang:str =arp.main_args["lang"]
    lang = lang.lower()
    if character == "符玄":
        async with aiofiles.open("/Users/whu/Downloads/sony2.wav", "rb") as f:
            wav_bytes = await f.read()
        duration = get_wav_duration(wav_bytes)
        mimetype = "audio/wav"
        await speak_test.finish(Voice(raw=wav_bytes, mimetype=mimetype, duration=duration))
    if character == "小桃" and text != "":
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"http://192.168.1.103:9880/tts?text={text}&text_lang={lang}&ref_audio_path=E:\AI\downloaded_sovits_models\momo%26midori-zh\momo\sound\main\879009.ogg_0000000000_0000159040.wav&prompt_lang=zh&prompt_text=想提高我的好感度，那就多买点新游戏吧。 &text_split_method=cut5&batch_size=1&media_type=wav&streaming_mode=false"
            response = await client.request("GET", url)
            wav_bytes = response.content
        duration = get_wav_duration(wav_bytes)
        mimetype = "audio/wav"
        await speak_test.finish(Voice(raw=wav_bytes, mimetype=mimetype, duration=duration))
    await speak_test.finish()