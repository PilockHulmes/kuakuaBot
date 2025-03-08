from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot import logger, on_command, on_regex, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from redis.asyncio import Redis
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.params import CommandArg
from nonebot.adapters import Message

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

import re

__plugin_meta__ = PluginMetadata(
    name="catms_boss_recruiter",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
    602682031,
    1020882307,
]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False
recruiter_help_usage = """命令清单（随时可能变）
发车命令：
.赛黑互带 Q2
这个命令会开一个赛黑互带车，车上还有2名额

查看板子上有哪些车：
.互带车
这个命令会让机器人回复所有三天之内有更新的车，在用了上述命令以后机器人会发如下回复：
1. 2025-03-09 12:42 @发布人1 Q2
2. 2025-03-08 09:52 @发布人2 Q3
...

自顶命令：
.赛黑自顶
只对发车人生效，会把你发的车的时间更新到最新，在别人问互带车时就会排到最上面

解散命令：
.赛黑解散
只对发车人生效，会把当前赛黑车解散

上车命令：
.赛黑上车 @发布人

下车命令：
.赛黑下车

以上所有“赛黑”打成“塞黑”也有用
"""
recruiter_help = on_command("招募板子", priority=15, block=True, rule=Rule(user_in_whitelist))
bm_carry_recruit = on_command("赛黑互带", aliases=["塞黑互带"], priority=15, block=True, rule=Rule(user_in_whitelist))
bm_carry_join = on_command("赛黑上车", aliases=["塞黑上车"], priority=15, block=True, rule=Rule(user_in_whitelist))
bm_carry_exit = on_command("赛黑下车", aliases=["塞黑下车"], priority=15, block=True, rule=Rule(user_in_whitelist))
bm_carry_bump = on_command("赛黑自顶", aliases=["塞黑自顶"], priority=15, block=True, rule=Rule(user_in_whitelist))
bm_carry_dismiss = on_command("赛黑解散", aliases=["塞黑解散"], priority=15, block=True, rule=Rule(user_in_whitelist))

@recruiter_help.handle()
async def handle(event:GroupMessageEvent):
    await recruiter_help.finish(recruiter_help_usage)

recruit_slots_regex = r"[Qq]([12345])"
@bm_carry_recruit()
async def handle(event:GroupMessageEvent, args: Message = CommandArg()):
    if slots := args.extract_plain_text():
        if not re.search(recruit_slots_regex, slots):
            bm_carry_recruit.finish("人数格式不对，支持 Q1 Q2 Q3 Q4 Q5")
        
    else:
        bm_carry_recruit.finish("请输入招募人数，例如 .赛黑互带 Q2")
        
    