from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot import logger, on_command, on_regex, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from redis.asyncio import Redis
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.rule import Rule
import re

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

__plugin_meta__ = PluginMetadata(
    name="catms_boss_notifier",
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
match_regex = r"(10|(?<!\d)[1-9])([Xx][Ll]|希拉|希腊|老女人|大眼墩子[Xx][Ll])"
notifier = on_regex(match_regex, priority=15, block=True, rule=Rule(group_in_whitelist))
list_add = on_command("希拉车加我", priority=15, block=True, rule=Rule(group_in_whitelist))
list_remove = on_command("希拉车删我", priority=15, block=True, rule=Rule(group_in_whitelist))

bm_match_regex = r"(10|(?<!\d)[1-9])(赛|塞)黑"
bm_notifier = on_regex(bm_match_regex, priority=15, block=True, rule=Rule(group_in_whitelist))
bm_list_add = on_command("赛黑车加我", aliases=set(["塞黑车加我"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_list_remove = on_command("赛黑车删我", aliases=set(["塞黑车删我"]), priority=15, block=True, rule=Rule(group_in_whitelist))

bm_carry_notifier = on_regex(r"[赛|塞]黑互带[Qq][1-5]", priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_asking = on_regex(r"[赛|塞]黑互带[.]{0,4}吗", priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_list_add = on_command("赛黑互带加我", aliases=set(["塞黑互带加我"]), priority=15, block=True, rule=Rule(group_in_whitelist))
bm_carry_list_remove = on_command("赛黑互带删我", aliases=set(["塞黑互带删我"]), priority=15, block=True, rule=Rule(group_in_whitelist))


import time
private_msg_whitelist = [
    392206976,
    # 528886033,
]
@notifier.handle()
async def handler(event:GroupMessageEvent, bot:OneBot):
    m = event.message.extract_plain_text()
    if not re.search(match_regex, m):
        await notifier.finish()
    group_id = event.group_id
    qqs = await chat_saver.listQQ(group_id)
    
    at_messages = ""
    for qq in qqs:
        at_messages += f" [CQ:at,qq={qq}]"
    
    send_message = f"""大佬发希拉车了，at 一下想上车的群友们，刷屏见谅哈。 {at_messages}
上车命令： .希拉车加我 .赛黑车加我 .赛黑互带加我
下车命令： .希拉车删我 .赛黑车删我 .赛黑互带删我"""
    
    if group_id in whiltelist:
        await bot.send_group_msg(group_id= group_id, message = send_message, auto_escape = False)
        for qq in private_msg_whitelist:
            if qq in qqs:
                await bot.send_private_msg(user_id=qq, message=m, auto_escape=True)
    await notifier.finish()

@list_add.handle()
async def handleAdd(event:GroupMessageEvent):
    if await chat_saver.hasQQ(event.group_id, event.user_id):
        await notifier.finish("已在希拉车提醒队列中，无需添加。需要下车请用 .希拉车删我")
    await chat_saver.addQQ(event.group_id, event.user_id)
    await notifier.finish("希拉车添加成功。需要下车请用 .希拉车删我")

@list_remove.handle()
async def handleRemove(event:GroupMessageEvent):
    if not await chat_saver.hasQQ(event.group_id, event.user_id):
        await notifier.finish("不在希拉车提醒队列中，无需删除")
    await chat_saver.removeQQ(event.group_id, event.user_id)
    await notifier.finish("希拉车删除成功")

bm_title = "bm_saved_id"
@bm_notifier.handle()
async def bmHandle(event:GroupMessageEvent, bot:OneBot):
    m = event.message.extract_plain_text()
    if not re.search(bm_match_regex, m):
        await bm_notifier.finish()
    group_id = event.group_id
    qqs = await chat_saver.listQQ(group_id, bm_title)

    at_messages = ""
    for qq in qqs:
        at_messages += f" [CQ:at,qq={qq}]"
    
    send_message = f"""大佬发赛黑车了，at 一下想上车的群友们，刷屏见谅哈。 {at_messages}
上车命令： .希拉车加我 .赛黑车加我 .赛黑互带加我
下车命令： .希拉车删我 .赛黑车删我 .赛黑互带删我"""
    if group_id in whiltelist:
        await bot.send_group_msg(group_id= group_id, message = send_message, auto_escape = False)
        for qq in private_msg_whitelist:
            if qq in qqs:
                await bot.send_private_msg(user_id=qq, message=m, auto_escape=True)
    await notifier.finish()

@bm_list_add.handle()
async def bmHandleAdd(event:GroupMessageEvent):
    if await chat_saver.hasQQ(event.group_id, event.user_id, bm_title):
        await notifier.finish("已在赛黑车提醒队列中，无需添加。需要下车请用 .赛黑车删我")
    await chat_saver.addQQ(event.group_id, event.user_id, bm_title)
    await notifier.finish("赛黑车添加成功。需要下车请用 .赛黑车删我")

@bm_list_remove.handle()
async def bmHandleRemove(event:GroupMessageEvent):
    if not await chat_saver.hasQQ(event.group_id, event.user_id, bm_title):
        await notifier.finish("不在赛黑车提醒队列中，无需删除")
    await chat_saver.removeQQ(event.group_id, event.user_id, bm_title)
    await notifier.finish("赛黑车删除成功")

bm_carry_title = "bm_carry_saved_id"
@bm_carry_notifier.handle()
async def bmCarryHandle(event:GroupMessageEvent, bot:OneBot):
    group_id = event.group_id
    qqs = await chat_saver.listQQ(group_id, bm_carry_title)
    print(qqs)
    at_messages = ""
    for qq in qqs:
        at_messages += f" [CQ:at,qq={qq}]"
    
    send_message = f"""大佬们开赛黑互带车了，at 一下想上车的群友们，刷屏见谅哈。 
{at_messages}
上车命令： .希拉车加我 .赛黑车加我 .赛黑互带加我
下车命令： .希拉车删我 .赛黑车删我 .赛黑互带删我"""
    if group_id in whiltelist:
        await bot.send_group_msg(group_id= group_id, message = send_message, auto_escape = False)
    await notifier.finish()

@bm_carry_list_add.handle()
async def bmCarryHandleAdd(event: GroupMessageEvent):
    if await chat_saver.hasQQ(event.group_id, event.user_id, bm_carry_title):
        await notifier.finish("已在赛黑互带车提醒队列中，无需添加。需要下车请用 .赛黑互带删我")
    await chat_saver.addQQ(event.group_id, event.user_id, bm_carry_title)
    total = await chat_saver.listQQ(event.group_id, bm_carry_title)
    message = "赛黑互带车添加成功。需要下车请用 .赛黑互带删我"
    if len(total) >= 6:
        message += f"\n已经有 {len(total)} 人想赛黑互带，可以考虑用自行开足。有需要可以用 赛黑互带Q1 at 互带组中的人"
    await notifier.finish(message)

@bm_carry_list_remove.handle()
async def bmCarryHandleRemove(event:GroupMessageEvent):
    if not await chat_saver.hasQQ(event.group_id, event.user_id, bm_carry_title):
        await notifier.finish("不在赛黑互带车提醒队列中，无需删除")
    await chat_saver.removeQQ(event.group_id, event.user_id, bm_carry_title)
    await notifier.finish("赛黑互带车删除成功")