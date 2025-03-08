from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot import logger, on_command, on_regex, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from redis.asyncio import Redis
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.params import CommandArg
from nonebot.adapters import Message
from nonebot.rule import Rule

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

from .recruiter_redis import operator

import re
import time
from datetime import datetime

__plugin_meta__ = PluginMetadata(
    name="catms_boss_recruiter",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
    # 602682031,
    # 1020882307,
]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False
recruiter_help_usage = """命令清单（随时可能变）
发车命令：
.赛黑互带发车 Q2
这个命令会开一个赛黑互带车，车上还有2名额

查看板子上有哪些车：
.赛黑互带车
这个命令会让机器人回复所有三天之内有更新的车，在用了上述命令以后机器人会发如下回复：
- 2025-03-09 12:42 车头1 4/6
- 2025-03-08 09:52 车头2 3/6
...

查看自己发布/加入的互带车有多少人了：
.赛黑互带验车
以上命令会返回车上人数以及昵称
.赛黑互带验车 qq
以上命令会返回车上人数以及qq号
.赛黑互带验车 出发
以上命令会返回车上人数，并且在人满时 at 所有车上人员

解散命令：
.赛黑互带解散
以上命令只对发车人生效，会把当前赛黑车解散并且 at 所有成员
.赛黑互带悄悄解散
以上命令只对发车人生效，会把当前赛黑车解散

上车命令：
.赛黑互带上车 @车头

下车命令：
.赛黑互带下车

以上所有“赛黑”打成“塞黑”也有用
"""
recruiter_help = on_command("赛黑互带帮助", priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_board = on_command("赛黑互带车", aliases=set(["塞黑互带车"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_recruit = on_command("赛黑互带", aliases=set(["塞黑互带"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_join = on_command("赛黑互带上车", aliases=set(["塞黑互带上车"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_leave = on_command("赛黑互带下车", aliases=set(["塞黑互带下车"]), priority=15, block=True, rule=Rule(group_in_whitelist))
# bm_carry_bump = on_command("赛黑自顶", aliases=["塞黑自顶"], priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_dismiss = on_command("赛黑互带解散", aliases=set(["塞黑互带解散"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_dismiss_quiet = on_command("赛黑互带悄悄解散", aliases=set(["塞黑互带悄悄解散"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_check = on_command("赛黑互带验车", aliases=set(["赛黑互带验车"]), priority=15, block=True, rule=Rule(group_in_whitelist))

@recruiter_help.handle()
async def handle1(event:GroupMessageEvent):
    await recruiter_help.finish(recruiter_help_usage)

recruit_slots_regex = r"[Qq]([12345])"
@bm_carry_recruit.handle()
async def handle2(event:GroupMessageEvent, args: Message = CommandArg()):
    if slots := args.extract_plain_text():
        matcher = re.search(recruit_slots_regex, slots)
        if matcher:
            slots = int(matcher.group(1))
            (is_succeed, message) = await operator.create(event.group_id, event.user_id, slots, event.sender.nickname)
            bm_carry_recruit.finish(message)
        else:
            bm_carry_recruit.finish("人数格式不对，支持 Q1 Q2 Q3 Q4 Q5")
    else:
        bm_carry_recruit.finish("请输入招募人数，例如 .赛黑互带 Q2")

def buildAt(qqs):
    members = info["members"]
    at_members = ""
    for member in qqs:
        at_members += f" [CQ:at,qq={member}]"
    return at_members

recruit_at_regex = r"\[CQ:at,qq=([0-9]+)\]"
@bm_carry_join.handle()
async def handle3(event:GroupMessageEvent, args: Message = CommandArg()):
    if at_info := args.extract_plain_text():
        matcher = re.search(recruit_at_regex, at_info)
        if matcher:
            target_qq = int(matcher.group(1))
            (slots, message) = await operator.join(event.group_id, event.user_id, target_qq)
            if slots < 0:
                bm_carry_join.finish(message)
            if slots > 0:
                bm_carry_join.finish(f"{message}, 目前车上人数 {6-slots}/6")
            if slots == 0:
                info = await operator.getJoined(event.group_id, event.user_id)
                members = info["members"]
                at_members = buildAt(members)
                bm_carry_join.finish(f"{message}, 车拼成了。 {at_members} 该出发了！")
            bm_carry_join.finish("代码出了点问题，请联系修复")
        else:
            bm_carry_join.finish("请在命令中 at 车头，例如 .赛黑上车 @狐狸皮")
    else:
        bm_carry_join.finish("请在命令中 at 车头，例如 .赛黑上车 @狐狸皮")

@bm_carry_leave.handle()
async def handle4(event:GroupMessageEvent):
    (succeed, message) = await operator.leave(event.group_id, event.user_id, event.sender.nickname)
    bm_carry_leave.finish(message)

@bm_carry_check.handle()
async def handle5(event:GroupMessageEvent, args:Message = CommandArg()):
    info = await operator.getJoined(event.group_id, event.user_id)
    cmd = args.extract_plain_text()
    if cmd.strip() == "出发" and info["slots"] == 0:
        at_members = buildAt(info["members"])
        bm_carry_check.finish(f"车头是 {info["head_nickname"]}，人满可以出发 {at_members}")
    elif (cmd.strip() == "qq" or cmd.strip() == "QQ"):
        members = ", ".join(info["members"])
        bm_carry_check.finish(f"车头是 {info["recruit_id"]}，车内人数 {6 - int(info["slots"])}/6，车上人员是 {members}")
    else:
        members = ", ".join(info["members_nickname"])
        bm_carry_check.finish(f"车头是 {info["head_nickname"]}，车内人数 {6 - int(info["slots"])}/6，车上人员是 {members}")

@bm_carry_dismiss.handle()
async def handle6(event:GroupMessageEvent):
    info = await operator.getJoined(event.group_id, event.user_id)
    (succeed, message) = await operator.dismiss(event.group_id, event.user_id)
    if not succeed:
        bm_carry_dismiss.finish(message)
    else:
        at_message = buildAt(info["members"])
        bm_carry_dismiss.finish(f"互带车已经解散，{at_message}")

@bm_carry_dismiss_quiet.handle()
async def handle7(event:GroupMessageEvent):
    info = await operator.getJoined(event.group_id, event.user_id)
    (succeed, message) = await operator.dismiss(event.group_id, event.user_id)
    if not succeed:
        bm_carry_dismiss.finish(message)
    else:
        bm_carry_dismiss.finish(f"互带车已经解散")

@bm_carry_board.handle()
async def handle8(event: GroupMessageEvent):
    infos = await operator.list(event.group_id)
    message = "赛黑互带车：\n"
    for info in infos:
        message += f"- {datetime.fromtimestamp(info["timeline"])} {info["head_nickname"]} {6 - int(info["slots"])}/6"