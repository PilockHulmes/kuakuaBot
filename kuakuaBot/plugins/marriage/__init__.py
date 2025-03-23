from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import logger, on_command, on_regex, require, get_bot
from nonebot.internal.adapter import Bot
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, Event, MessageSegment
import httpx
import ssl
import json
from datetime import datetime
import base64

from .config import Config

from PIL import Image
from io import BytesIO

__plugin_meta__ = PluginMetadata(
    name="marriage",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

group_whitelist = [853041949, 1020882307, 244960293]
async def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

marriage = on_command("结婚", priority=15, rule=Rule(group_in_whitelist))

@marriage.handle()
async def _(event: GroupMessageEvent):
    print(event.message)
    image_url = ""
    for seg in event.message:
        if seg.type == "image":
            url = seg.data.get("url")
            if url:
                image_url = url
        if seg.type == "face":
            url = seg.data.get("url")
            if url:
                image_url = url
        if seg.type == "mface":
            url = seg.data.get("url")
            if url:
                image_url = url
    if image_url == "":
        await marriage.finish("未识别到图片")
    print(image_url)
    background = await load_image_from_url(image_url) 
    foreground = Image.open("./plugins/marriage/assets/jiehun.png").convert("RGBA")
    
    # 获取图片 B 的分辨率（目标分辨率）
    target_size = foreground.size  # (width, height)

    # 将图片 A 拉伸/压缩到与图片 B 相同分辨率
    # 使用高质量的抗锯齿算法（Image.LANCZOS）
    resized_background = background.resize(target_size, Image.Resampling.LANCZOS)
    # 直接叠加图片 B 到调整后的图片 A 上
    combined = Image.alpha_composite(resized_background, foreground)
    combined.save(f"./plugins/marriage/tmp/{event.user_id}.png", format="PNG")
    at_seg = MessageSegment.at(event.user_id)
    with open(f"./plugins/marriage/tmp/{event.user_id}.png", "rb") as f:
        img_data = f.read()
        base64_str = base64.b64encode(img_data).decode()
    img_seg = MessageSegment.image(f"base64://{base64_str}", timeout=30)
    await marriage.finish(at_seg + img_seg)

async def load_image_from_url(url):
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")  # 从默认的 2 降为 1
    async with httpx.AsyncClient(timeout=30, verify=ssl_context) as client:
        response = await client.get(url)
        return Image.open(BytesIO(response.content)).convert("RGBA")

def resize_crop_to_target(img, target_size):
    # 计算缩放比例，优先满足宽度或高度的较大边
    width, height = target_size
    img_ratio = img.width / img.height
    target_ratio = width / height

    if img_ratio > target_ratio:
        # 按宽度缩放，高度可能不足，后续裁剪
        new_height = int(width / img_ratio)
        resized = img.resize((width, new_height))
    else:
        # 按高度缩放，宽度可能不足，后续裁剪
        new_width = int(height * img_ratio)
        resized = img.resize((new_width, height))

    # 居中裁剪到目标尺寸
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    right = left + width
    bottom = top + height
    return resized.crop((left, top, right, bottom))