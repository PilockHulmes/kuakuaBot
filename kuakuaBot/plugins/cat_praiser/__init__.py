from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import require
from nonebot import on_message
from nonebot.rule import Rule
from nonebot import logger

from .config import Config

import time

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

whiltelist = [853041949]
miaowuwu = 28369507
def user_in_whitelist(event: GroupMessageEvent):
    return (event.group_id in whiltelist) and (event.user_id == miaowuwu)

start = time.time()
praise_interval = 180 # 先暂定三分钟一次
def praiser_interval(event: GroupMessageEvent):
    if time.time() - start > praise_interval:
        return True
    else:
        return False

praiser = on_message(priority=10, rule=Rule(user_in_whitelist) & Rule(praiser_interval), block=False)

message_countdown_cooldown = 10 # 每隔几句话夸一次，避免夸的太频繁
message_countdown = 0
@praiser.handle()
async def handle(event: GroupMessageEvent):
    if message_countdown > 0: # 避免复读太多次，所以
        message_countdown -= 1
        await praiser.finish()
    
    messages = await chat_saver.getLatestMessagesForRepeater(event.group_id, message_count=10, duration_in_secods=60)
    if messages[-1]["sender_id"] != miaowuwu: # 如果最后一条不是喵呜，说明还没来得及储存，再取一次。这里先不用循环了避免出问题死循环
        time.sleep(0.5)
        messages = await chat_saver.getLatestMessagesForRepeater(event.group_id, message_count=10, duration_in_secods=60)
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
        await repeater.finish()
    logger.info(all_messages)
    kuakua_message = miaowu_kuakua(all_messages)
    if kuakua_message == "":
        await praiser.finish()
    start = time.time()
    message_countdown = message_countdown_cooldown
    praiser.finish() # TODO: 改成发 kuakua_message