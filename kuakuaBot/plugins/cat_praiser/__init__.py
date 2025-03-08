from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import require
from nonebot import on_message
from nonebot.rule import Rule
from nonebot import logger

from .config import Config

import time
from datetime import datetime

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver
require("ask_deepseek")
from plugins.ask_deepseek.kuakua import miaowu_kuakua

__plugin_meta__ = PluginMetadata(
    name="cat_praiser",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
    # (853041949, 28369507), # 喵群，喵呜
    # (1020882307, 392206976), # 夸夸测试群，皮
]
def user_in_whitelist(event: GroupMessageEvent):
    for (group_id, user_id) in whiltelist:
        if event.group_id == group_id and event.user_id == user_id:
            return True
    return False

start = time.time()
praise_interval = 180 # 先暂定三分钟一次
def praiser_interval(event: GroupMessageEvent):
    global start
    if time.time() - start > praise_interval:
        return True
    else:
        return False

praiser = on_message(priority=10, rule=Rule(user_in_whitelist), block=False)

message_countdown_cooldown = 1 # 每隔几句话夸一次，避免夸的太频繁
message_countdown = {}
praise_interval = 5
praise_last_time = {}
@praiser.handle()
async def handle(event: GroupMessageEvent):
    global praise_last_time
    global message_countdown
    
    mix_id = (event.group_id, event.user_id)
    # 初始化一下，第一次满足条件的都不会夸
    if mix_id not in praise_last_time:
        praise_last_time[mix_id] = time.time()
    if mix_id not in message_countdown:
        message_countdown[mix_id] = message_countdown_cooldown

    # 避免复读太多次，所以用时间和次数限制一下
    if message_countdown[mix_id] > 0: 
        message_countdown[mix_id] -= 1
        await praiser.finish()
    if time.time() - praise_last_time[mix_id] < praise_interval:
        await praiser.finish()

    messages = await chat_saver.getLatestMessagesForRepeater(event.group_id, message_count=10, duration_in_secods=300)
    print(messages, event.group_id)
    if len(messages) == 0 or messages[-1]["sender_id"] != event.user_id: # 如果最后一条不是白名单人员，说明还没来得及储存，再取一次。这里先不用循环了避免出问题死循环
        time.sleep(0.5)
        messages = await chat_saver.getLatestMessagesForRepeater(event.group_id, message_count=10, duration_in_secods=300)
    all_messages = ""
    message_map = {}
    for i in range(len(messages)):
        message = messages[i]
        sender_id = message["sender_id"]
        timestamp = message["timestamp"]
        content = message["content"]
        all_messages += f"[消息{i}] [用户{sender_id}] [时间戳 {datetime.fromtimestamp(timestamp / 1000)}]: {content}\n"
        message_map[f"消息{i}"] = message
    if all_messages.strip() == "":
        await praiser.finish()
    logger.info(all_messages)
    kuakua_message = await miaowu_kuakua(event.user_id, all_messages)
    if kuakua_message == "":
        await praiser.finish()
    praise_last_time[mix_id] = time.time()
    message_countdown[mix_id] = message_countdown_cooldown
    await praiser.finish() # TODO: 改成发 kuakua_message