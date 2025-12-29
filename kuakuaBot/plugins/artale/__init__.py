from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

import asyncio
from .config import Config
from nonebot import logger, on_command, on_regex, require, get_bot, get_driver
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from redis.asyncio import Redis
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.rule import Rule
import re
from redis.asyncio import Redis
from nonebot.adapters import Message
from nonebot.params import CommandArg
import signal
from .message_filter import MessageFilter

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


__plugin_meta__ = PluginMetadata(
    name="artale",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
    1020882307,
    853248277,
]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

async def listen_redis_channel():
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    async with redis.pubsub() as pubsub:
        await pubsub.subscribe("smega_content")
        logger.info("subsribe smega successfully")
        
        def signal_handler(sig, frame):
            print("\n收到中断信号，取消订阅...")
            pubsub.unsubscribe('my_channel')
        signal.signal(signal.SIGINT, signal_handler)  # 注册信号处理函数

        try:
            async for message in pubsub.listen():
                try:
                    if message["type"] == "message":
                        data = message["data"]
                        await handle_smega_message(data)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error in pubsub listen: {e}")


keywords_map = {}
async def handle_smega_message(data: str):
    if await message_filter.is_message_processed(data):
        return
    await message_filter.add_message_processed(data)

    parts = re.split(r'(CH.*?[:：：])', data, maxsplit=1)
    if len(parts) != 3:
        logger.info(f"get wrong message: {data}")
    else:
        name = parts[0]
        channel = parts[1]
        text = parts[2]
        bot = get_bot()
        for group in whiltelist:
            users = await message_filter.process_message(group, text)
            if users is None or len(users) == 0:
                continue
            logger.info(users)
            at_messages = ""
            for user in users:
                at_messages += f" [CQ:at,qq={user}]"
            send_message = f"""{at_messages}
喇叭有新的关注内容：
{name} : {text} 
"""
            print(group, send_message)
            await bot.send_group_msg(group_id=group, message = send_message, auto_escape = False)
    return

# uncomment to make it work
# driver = get_driver()
# @driver.on_bot_connect
async def bot_connect():
    try:
        await listen_redis_channel()
    except Exception as e:
        logger.error(f"获取 bot 失败，稍后重试：{e}")

message_filter = MessageFilter()
add_keyword = on_command("关注卖货", aliases=set(["關注賣貨", "關注買貨"]), priority=15, block=True, rule=Rule(group_in_whitelist))
remove_keyword = on_command("取消关注卖货", aliases=set(["取消關注賣貨", "取消關注買貨"]), priority=15, block=True, rule=Rule(group_in_whitelist))
clear_keyword = on_command("清空卖货", aliases=set(["清空賣貨", "清空買貨"]), priority=15, block=True, rule=Rule(group_in_whitelist))
list_keyword = on_command("查看关注清单", aliases=set(["查看關注清單"]), priority=15, block=True, rule=Rule(group_in_whitelist))
enable_notification = on_command("启用提示", aliases=set(["啓用提示"]), priority=15, block=True, rule=Rule(group_in_whitelist))
disable_notification = on_command("禁用提示", aliases=set(["禁用提示"]), priority=15, block=True, rule=Rule(group_in_whitelist))

@add_keyword.handle()
async def _(event: GroupMessageEvent, bot: OneBot, args: Message = CommandArg()):
    keywords = args.extract_plain_text().strip().split(" ")
    for keyword in keywords:
        await message_filter.add_user_keyword(event.group_id, event.user_id, keyword)
    message = f"[CQ:at,qq={event.user_id}] 关注成功"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()

@remove_keyword.handle()
async def _(event: GroupMessageEvent, bot: OneBot, args: Message = CommandArg()):
    keywords = args.extract_plain_text().strip().split(" ")
    for keyword in keywords:
        await message_filter.remove_user_keyword(event.group_id, event.user_id, keyword)
    message = f"[CQ:at,qq={event.user_id}] 取消成功"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()

@clear_keyword.handle()
async def _(event: GroupMessageEvent, bot: OneBot):
    await message_filter.clear_user_keywords(event.group_id, event.user_id)
    message = f"[CQ:at,qq={event.user_id}] 清空成功"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()

@list_keyword.handle()
async def _(event: GroupMessageEvent, bot: OneBot):
    keywords = await message_filter.get_user_keywords(event.group_id, event.user_id)
    joied_keywords = " ".join(keywords)
    message = f"[CQ:at,qq={event.user_id}] 已关注以下关键字：{joied_keywords}"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()

@enable_notification.handle()
async def _(event: GroupMessageEvent, bot: OneBot):
    await message_filter.active_user(event.group_id, event.user_id)
    message = f"[CQ:at,qq={event.user_id}] 已启用喇叭提示"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()

@disable_notification.handle()
async def _(event: GroupMessageEvent, bot: OneBot):
    await message_filter.pause_user(event.group_id, event.user_id)
    message = f"[CQ:at,qq={event.user_id}] 已禁用喇叭提示"
    await bot.send_group_msg(group_id=event.group_id, message = message, auto_escape = False)
    await add_keyword.finish()