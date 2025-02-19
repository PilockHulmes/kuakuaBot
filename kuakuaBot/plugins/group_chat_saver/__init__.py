from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="group_chat_saver",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [853041949, 1020882307]
async def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

