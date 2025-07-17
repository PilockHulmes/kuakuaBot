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


group_whitelist = [1020882307, 853041949, 244960293,1047606702]
def group_in_whitelist(event: GroupMessageEvent):
    return event.group_id in group_whitelist

qq_whitelist = [392206976, 28369507, 875960021]
def qq_in_whitelist(event: GroupMessageEvent):
    return event.user_id in qq_whitelist


add_person = on_command("关注主播", priority=15, block=True, rule=Rule(group_in_whitelist) & Rule(qq_in_whitelist))
remove_person = on_command("取关主播", priority=15, block=True, rule=Rule(group_in_whitelist) & Rule(qq_in_whitelist))
streaming_status = on_command("直播情况", aliases=set(["有谁在直播","直播"]), priority=15, block=True, rule=Rule(group_in_whitelist))

streaming_api_base = "https://api.live.bilibili.com/room/v1/Room/get_info"
streaming_batch_get_info_base = 'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids' # POST 
streaming_up_info_base = "https://api.live.bilibili.com/live_user/v1/Master/info"
saved_title = "polling_uids"

async def getStreamingRoomsByUIDs(uids):
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{streaming_batch_get_info_base}"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
            "User-Agent": "PostmanRunime/7.43.2",
            "Content-Type": "application/json"
        }
        payload = {
            "uids": uids
        }
        response = await client.request("POST", url=url,json=payload,headers=headers, timeout=30)
        response_obj = json.loads(response.text)
        return response_obj

@add_person.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    uid = args.extract_plain_text().strip()
    if await has_streaming(event.group_id, uid, saved_title):
        await add_person.finish("已经关注了该主播")
    if uid is None or not uid.isnumeric():
        await add_person.finish("请输入格式正确的UID，例如 .关注主播 123")
    room_info = await getStreamingRoomsByUIDs([int(uid)])
    if room_info["code"] != 0 or room_info["msg"] != "success":
        await add_person.finish(room_info["msg"])
    else:
        await add_streaming(event.group_id, uid, saved_title)
        await add_person.finish(f"关注成功，若要取关请用 .取关主播 {uid}")

@remove_person.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    room_id = args.extract_plain_text().strip()
    if room_id is None or not room_id.isnumeric():
        await remove_person.finish("请输入格式正确的UID，例如 .取关主播 123")
    if not await has_streaming(event.group_id, room_id, saved_title):
        await remove_person.finish("取关失败，未关注该主播")
    await remove_streaming(event.group_id, room_id, saved_title)
    await remove_person.finish("取关成功")

@streaming_status.handle()
async def _(event: GroupMessageEvent):
    uids = await list_streaming(event.group_id, saved_title)
    if len(uids) == 0:
        await streaming_status.finish("没有关注任何主播，请用 .关注主播 UID 来进行关注")
    room_infos = await getStreamingRoomsByUIDs(uids)
    if room_infos["code"] != 0: # 没有成功获取直播间信息则跳过
        await streaming_status.finish(f"获取直播信息失败，失败原因: {room_infos["msg"]}")
    streaming_rooms = []
    for uid in uids:
        if str(uid) not in room_infos["data"]:
            continue
        room_info = room_infos["data"][str(uid)]
        live_timestamp = room_info["live_time"]
        if int(live_timestamp) > 0:
            room_id = room_info["room_id"]
            streaming_rooms.append(f"{await getNameByUID(uid)} http://live.bilibili.com/{room_id}")
    if len(streaming_rooms) == 0:
        await streaming_status.finish(f"目前无人直播")
    else:
        response = "以下主播正在直播:\n"
        response += "\n".join(streaming_rooms)
        await streaming_status.finish(response)

def calculate_time_difference(timestamp):
    # 解析日期字符串
    target_time = datetime.fromtimestamp(int(timestamp))
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
        }, timeout=30)
        response_obj = json.loads(response.text)
        if response_obj["code"] != 0:
            return ""
        streaming_name[uid] = response_obj["data"]["info"]["uname"]
        return response_obj["data"]["info"]["uname"]

streaming_on = {}
@scheduler.scheduled_job("cron", second="*/20", misfire_grace_time=5) # 每隔 20 秒检查一次
async def poll_steaming_condition():
    logger.info("Streaming polling...")
    bot: Bot = get_bot()
    poll_start = datetime.now().timestamp()
    for group_id in group_whitelist:
        if group_id not in streaming_on:
            streaming_on[group_id] = {}
        uids = await list_streaming(group_id, saved_title)
        if uids is None or len(uids) == 0:
            continue
        room_infos = await getStreamingRoomsByUIDs(uids)
        if room_infos["code"] != 0: # 没有成功获取直播间信息则跳过
            continue
        for uid in uids:
            if str(uid) not in room_infos["data"]:
                continue
            room_info = room_infos["data"][str(uid)]
            live_timestamp = room_info["live_time"]
            # 若直播间未开播，则判断是否需要做下播通知，并跳过
            if live_timestamp == 0: #
                if uid in streaming_on[group_id] and streaming_on[group_id][uid]:
                    await bot.call_api("send_group_msg", group_id=group_id, message = f"{await getNameByUID(uid)}已下播")
                    streaming_on[group_id][uid] = False
                continue
            
            # 若已开播，则只为一分钟内开播且没有通知过的直播间做开播通知。
            (is_past, diff_seconds) = calculate_time_difference(live_timestamp)
            if not is_past:
                logger.warning(f"获取到开播时间晚于当前时间的直播: {uid}")
                continue
            if uid in streaming_on[group_id] and streaming_on[group_id][uid]:
                continue
            if diff_seconds > 120:
                continue
            streaming_on[group_id][uid] = True
            img = MessageSegment.image(room_info["cover_from_user"], timeout=30)
            room_id = room_info["room_id"]
            texts = MessageSegment.text(f"{await getNameByUID(uid)}的直播间已开播，地址 http://live.bilibili.com/{room_id}")
            await bot.call_api("send_group_msg", group_id=group_id, message = img + texts)
    (_, poll_total_seconds) = calculate_time_difference(poll_start)
    logger.info(f"poll costs {poll_total_seconds}s")