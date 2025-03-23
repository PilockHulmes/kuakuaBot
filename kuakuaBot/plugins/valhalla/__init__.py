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

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

group_whitelist = []
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

qq_whitelist = [392206976]
def qq_in_whitelist(event: GroupMessageEvent):
    return event.user_id in qq_whitelist

watch_group = on_command("启用英灵殿", aliases=set(["valhalla", "瓦尔哈拉"]), priority=15, rule=Rule(qq_in_whitelist))
unwatch_group = on_command("关闭英灵殿", priority=15, rule=Rule(qq_in_whitelist))

valhalla_groups_title = "groups_enable_valhalla"
valhalla_mocked_group = -1 



@watch_group.handle()
async def _(event: GroupMessageEvent):
    if await chat_saver.hasQQ(valhalla_mocked_group, event.group_id, valhalla_groups_title):
        await watch_group.finish("已启用")
    await chat_saver.addQQ(valhalla_mocked_group, event.group_id, valhalla_groups_title)
    await fetchQQForGroup(event.group_id)
    await watch_group.finish("成功启用英灵殿，随时准备召回英灵")

@unwatch_group.handle()
async def _(event: GroupMessageEvent):
    if not await chat_saver.hasQQ(valhalla_mocked_group, event.group_id, valhalla_groups_title):
        await watch_group.finish("未启用英灵殿，无需关闭")
    await chat_saver.removeQQ(valhalla_mocked_group, event.group_id, valhalla_groups_title)
    await watch_group.finish("成功关闭英灵殿")

async def fetchQQForGroup(group_id):
    bot: Bot = get_bot()
    members = await bot.call_api("get_group_member_list", group_id=group_id, cache=False)
    member_qqs = [str(m["user_id"]) for m in members]
    print(member_qqs)
    if len(member_qqs) > 0:
        await chat_saver.saveQQInfo(valhalla_mocked_group, group_id, ",".join(member_qqs), valhalla_groups_title)

@scheduler.scheduled_job("cron", day="*", misfire_grace_time=5) # 每天同步一次 QQ 号
async def fetchQQForGroups():
    groups = await chat_saver.listQQ(valhalla_mocked_group, valhalla_groups_title)
    for group_id in groups:
        await fetchQQForGroup(group_id)