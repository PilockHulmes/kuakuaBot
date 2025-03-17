from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import logger, on_command, on_regex, require, get_bot
from nonebot.internal.adapter import Bot
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, Event, MessageSegment
import httpx
import json
from datetime import datetime
import brotli

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
require("group_chat_saver")
from plugins.group_chat_saver.redis.chatsaver import chat_saver

# 逻辑可以共用，但 chat_saver 里的方法名带 QQ 容易引起歧义，所以重命名一次
list_streaming = chat_saver.listQQ
add_streaming = chat_saver.addQQ
has_streaming = chat_saver.hasQQ
remove_streaming = chat_saver.removeQQ
save_streaming_info = chat_saver.saveQQInfo
get_streaming_info = chat_saver.getQQInfo

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="bilibili_streaming_notification",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


group_whitelist = [1020882307, 853041949, 244960293]
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

qq_whitelist = [392206976, 28369507, 875960021]
def qq_in_whitelist(event: GroupMessageEvent):
    return event.user_id in qq_whitelist


add_room = on_command("关注直播间", priority=15, block=True, rule=Rule(group_in_whitelist) & Rule(qq_in_whitelist))
remove_room = on_command("取关直播间", priority=15, block=True, rule=Rule(group_in_whitelist) & Rule(qq_in_whitelist))

streaming_api_base = "https://api.live.bilibili.com/room/v1/Room/get_info"
streaming_up_info_base = "https://api.live.bilibili.com/live_user/v1/Master/info"
saved_title = "polling_rooms"

async def getRoomInfo(room_id):
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{streaming_api_base}?room_id={room_id}"
        response = await client.request("GET", url=url,headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
            "User-Agent": "PostmanRunime/7.43.2",
        })
        response_obj = json.loads(response.text)
        return response_obj

@add_room.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    room_id = args.extract_plain_text().strip()
    if room_id is None or not room_id.isnumeric():
        await add_room.finish("请输入格式正确的直播间地址，例如 .关注直播间 123")
    room_info = await getRoomInfo(room_id)
    if room_info["code"] != 0 or room_info["msg"] != "ok":
        await add_room.finish(room_info["msg"])
    else:
        await add_streaming(event.group_id, room_id, saved_title)
        await add_room.finish(f"关注成功，若要取关请用 .取关直播间 {room_id}")

@remove_room.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    room_id = args.extract_plain_text().strip()
    if room_id is None or not room_id.isnumeric():
        await remove_room.finish("请输入格式正确的直播间地址，例如 .关注直播间 123")
    if not await has_streaming(event.group_id, room_id, saved_title):
        await remove_room.finish("取关失败，未关注该直播间")
    await remove_streaming(event.group_id, room_id, saved_title)
    await remove_room.finish("取关成功")

def calculate_time_difference(date_str):
    # 解析日期字符串
    target_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    # 获取当前时间
    current_time = datetime.now()
    # 计算时间差
    delta = target_time - current_time
    total_seconds = delta.total_seconds()
    
    # 判断时间是否过去
    is_past = total_seconds < 0
    total_seconds = abs(total_seconds)  # 取绝对值计算时间差
    return (is_past, int(total_seconds))

streaming_name = {}
async def getNameByUID(uid: int):
    if uid in streaming_name:
        return streaming_name[uid]
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{streaming_up_info_base}?uid={uid}"
        response = await client.request("GET", url=url,headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
            "User-Agent": "PostmanRunime/7.43.2",
        })
        response_obj = json.loads(response.text)
        if response_obj["code"] != 0:
            return ""
        streaming_name[uid] = response_obj["data"]["info"]["uname"]
        return response_obj["data"]["info"]["uname"]

streaming_on = {}
@scheduler.scheduled_job("cron", second=1, misfire_grace_time=5) # 每隔 20 秒检查一次
async def poll_steaming_condition():
    logger.info("Streaming polling...")
    bot: Bot = get_bot()
    poll_start = datetime.now()
    for group_id in group_whitelist:
        if group_id not in streaming_on:
            streaming_on[group_id] = {}
        room_ids = await list_streaming(group_id, saved_title)
        for room_id in room_ids:
            room_info = await getRoomInfo(room_id)
            if room_info["code"] != 0 or room_info["msg"] != "ok":# 没有该直播间则跳过
                continue
            uid = room_info["data"]["uid"]
            
            streaming_time_str = room_info["data"]["live_time"]
            # 若直播间未开播，则判断是否需要做下播通知，并跳过
            if streaming_time_str.startswith("0000-00-00"): # 特殊字符串，中间的空格和键盘上的不太一样，总之复制黏贴一个过来就行
                if room_id in streaming_on[group_id] and streaming_on[group_id][room_id]:
                    await bot.call_api("send_group_msg", group_id=group_id, message = f"{await getNameByUID(uid)}已下播")
                    streaming_on[group_id][room_id] = False
                continue
            
            # 若已开播，则只为一分钟内开播且没有通知过的直播间做开播通知。
            (is_past, diff_seconds) = calculate_time_difference(streaming_time_str)
            if not is_past:
                logger.warning(f"获取到开播时间晚于当前时间的直播: {room_id}")
                continue
            if room_id in streaming_on[group_id] and streaming_on[group_id][room_id]:
                continue
            if diff_seconds > 180:
                continue
            streaming_on[group_id][room_id] = True
            img = MessageSegment.image(room_info["data"]["user_cover"])
            texts = MessageSegment.text(f"{await getNameByUID(uid)}的直播间已开播，地址 http://live.bilibili.com/{room_id}")
            await bot.call_api("send_group_msg", group_id=group_id, message = img + texts)
    (_, poll_total_seconds) = calculate_time_difference(poll_start.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info(f"poll costs {poll_total_seconds}s")