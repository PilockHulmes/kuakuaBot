from nonebot import get_plugin_config, logger ,require
from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.rule import Rule


# from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, Event
from nonebot.adapters.onebot.v11 import MessageSegment, Message

from .config import Config

from PIL import Image

__plugin_meta__ = PluginMetadata(
    name="pm_collect_info",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

pm_collect = on_message(rule=to_me(), priority=10)

require("nonebot_plugin_what2eat")
from repo_plugins.nonebot_plugin_what2eat.nonebot_plugin_what2eat.data_source import eating_manager
from repo_plugins.nonebot_plugin_what2eat.nonebot_plugin_what2eat.utils import Meals

@pm_collect.handle()
async def _(event: PrivateMessageEvent):
    if event.user_id == 392206976:
        logger.info(event.message)
        
    # await eating_manager.do_greeting(Meals.BREAKFAST)
    
    await pm_collect.finish()