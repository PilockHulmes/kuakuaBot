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

require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
import re

import signal

__plugin_meta__ = PluginMetadata(
    name="artale",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

async def listen_redis_channel(bot):
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
                        await handle_smega_message(bot, data)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error in pubsub listen: {e}")


async def handle_smega_message(bot, data):
    parts = re.split(r'(CH.*?[:：：])', data, maxsplit=1)
    if len(parts) != 3:
        logger.info(f"get wrong message: {data}")
    else:
        logger.info(f"{parts[0]} smega {parts[2]}")
    return

driver = get_driver()
@driver.on_bot_connect
async def bot_connect():
    try:
        bot = get_bot()
        await listen_redis_channel(bot)
    except Exception as e:
        logger.error(f"获取 bot 失败，稍后重试：{e}")

