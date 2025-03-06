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
from plugins.ask_deepseek.prompt import send_repeater_messages_v3
globals 
__plugin_meta__ = PluginMetadata(
    name="repeater",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [853041949, 1020882307, 244960293]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

start = {}
repeat_interval = 60
# initial_wait_time = 10 * 60
initial_wait_time = 0
def repeater_interval(event: GroupMessageEvent):
    global start
    group_id = event.get_session_id()
    if group_id in start:
        logger.info(f"{group_id} 还剩 {repeat_interval - (time.time() - start[group_id])}")
    if group_id not in start:
        start[group_id] = time.time() + initial_wait_time # 启动以后等一段时间再开始复读，因为需要时间收集聊天记录
        return False
    elif time.time() - start[group_id] > repeat_interval:
        start[group_id] = time.time()
        return True
    else:
        return False

repeater = on_message(priority=10, rule=Rule(group_in_whitelist) & Rule(repeater_interval), block=False)

repeated_messages = {}
@repeater.handle()
async def handle(event: GroupMessageEvent):
    messages = await chat_saver.getLatestMessagesForRepeater(event.group_id, message_count=5, duration_in_secods=repeat_interval)
    # 一分钟说不到几条也就别花 token 检查了。先这么看看频率
    if len(messages) <= 3:
        logger.info("chat frequency too low, skip repeater")
        await repeater.finish()
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
    analyze_result = await send_repeater_messages_v3(all_messages)
    if isinstance(analyze_result, str):
        await repeater.finish()
    for message, analyze in analyze_result.items():
        if analyze == "":
            continue
        score = int(analyze.split(" ")[0])
        print(message, score, message_map[message]["content"], score >= 80)
        if score >= 80:
            # 检查有没有复读过
            if event.group_id not in repeated_messages:
                repeated_messages[event.group_id] = []
                await repeater.finish(message_map[message]["content"])
            else:
                if message_map[message]["msg_id"] in repeated_messages[event.group_id]:
                    logger.info("skip repeating message since the message have already been repeated")
                    await repeater.finish()
                else:
                    repeated_messages[event.group_id].append(message_map[message]["msg_id"])
                    repeated_messages[event.group_id][-20:] # 只保留最近 20 条复读过的消息 id
                    await repeater.finish(message_map[message]["content"])
            
    await repeater.finish()