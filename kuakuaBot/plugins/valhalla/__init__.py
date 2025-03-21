from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import logger, on_command, on_regex, require, get_bot
from nonebot.internal.adapter import Bot
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, Event, MessageSegment
import httpx
import json
from datetime import datetime

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="valhalla",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

group_whitelist = []
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

qq_whitelist = [392206976]
def qq_in_whitelist(event: GroupMessageEvent):
    return event.user_id in qq_whitelist

watch_group = on_command("启用英灵殿", priority=15, rule=Rule(qq_in_whitelist))

@watch_group.handle()
async def _(event: GroupMessageEvent):
    