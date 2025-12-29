from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import logger, on_command, on_regex, require, get_bot, on_message
from nonebot.internal.adapter import Bot
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, Event, MessageSegment
import httpx
import json
from datetime import datetime
import time
import random
from pathlib import Path
import base64

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="hachimi_ha",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

group_whitelist = [
    244960293,
    # 1020882307,
]
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

qq_whitelist = [
    506604898, 
    392206976,
]
def qq_in_whitelist(event: GroupMessageEvent):
    return event.user_id in qq_whitelist

HA_INTERVAL = 600
group_cooldown = {}
def on_cooldown(event: GroupMessageEvent):
    if event.group_id in group_cooldown:
        print(group_cooldown[event.group_id], time.time())
    if event.group_id not in group_cooldown:
        group_cooldown[event.group_id] = time.time()
        return True
    if group_cooldown[event.group_id] + HA_INTERVAL > time.time():
        logger.info("ha on cooldown")
        return False
    else:
        group_cooldown[event.group_id] = time.time()
        return True

HA_RATE = 0.006
def should_ha():
    rand_num = random.random()
    logger.info(f"get rand_num {rand_num} and rate {HA_RATE}")
    return rand_num < HA_RATE

ha = on_message(rule= Rule(group_in_whitelist) & Rule(should_ha), priority=5, block=True) # 哈气的时候拒绝其他服务

HA_IMAGES_FOLDER = Path("./plugins/hachimi_ha/assets")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
@ha.handle()
async def _(event: GroupMessageEvent):
    # if not on_cooldown(event):
    #     await ha.finish()
    image_files = [f for f in HA_IMAGES_FOLDER.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not image_files:
        await ha.finish()
    
    # 随机选择一张图片
    selected_image = random.choice(image_files)
    with open(selected_image, "rb") as f:
        img_data = f.read()
        base64_str = base64.b64encode(img_data).decode()
       # 构建图片消息
    # image_msg = MessageSegment.image(selected_image)
    img_seg = MessageSegment.image(f"base64://{base64_str}", timeout=30)
    
    # 发送图片
    await ha.finish(img_seg)