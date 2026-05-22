"""
content_echo — 重复内容检测 & 图片回复插件

监听白名单群的转发/图片/视频消息，计算内容 checksum 存入 Redis。
当相同内容在短时间内再次出现时（消息计数差 ≤ threshold），自动发送指定图片。
"""

import hashlib
import time
from typing import Optional

from nonebot import get_plugin_config, logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.plugin import PluginMetadata
from nonebot import on_command, on_message
from nonebot.rule import Rule

from .config import Config
from .redis_handler import content_echo_redis

__plugin_meta__ = PluginMetadata(
    name="content_echo",
    description="重复内容检测 - 检测群内重复的转发/图片/视频并发送图片",
    usage="自动监听；发送「开启复读提示」「关闭复读提示」控制开关",
    config=Config,
)

config = get_plugin_config(Config)


# =============================================================================
# 群白名单
# =============================================================================

def group_in_whitelist(event: Event) -> bool:
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in config.group_whitelist
    return False


# =============================================================================
# 消息监听
# =============================================================================

echo = on_message(
    priority=10,
    rule=Rule(group_in_whitelist),
    block=False,
)


# =============================================================================
# 开关命令
# =============================================================================

echo_on = on_command(
    "开启复读提示",
    priority=10,
    block=True,
    rule=Rule(group_in_whitelist),
)

echo_off = on_command(
    "关闭复读提示",
    priority=10,
    block=True,
    rule=Rule(group_in_whitelist),
)


@echo_on.handle()
async def handle_echo_on(bot: Bot, event: GroupMessageEvent):
    await content_echo_redis.set_enabled(event.group_id, True)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=MessageSegment.text("✅ 复读提示已开启"),
    )
    await echo_on.finish()


@echo_off.handle()
async def handle_echo_off(bot: Bot, event: GroupMessageEvent):
    await content_echo_redis.set_enabled(event.group_id, False)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=MessageSegment.text("⏸️ 复读提示已关闭"),
    )
    await echo_off.finish()


# =============================================================================
# Checksum 计算
# =============================================================================

def _extract_node_text(node: dict) -> str:
    """
    从 get_forward_msg 返回的单个消息节点中提取文本内容。

    不同适配器返回的字段名可能不同（content / message），
    值可能是 str（纯文本）或 list[dict]（消息段数组）。
    对嵌套转发：跳过（不递归获取，避免 ID 变化导致 checksum 不一致）。
    """
    # 兼容不同适配器的字段名：content（多数实现）或 message
    msg = node.get("content") or node.get("message", "")
    if isinstance(msg, str):
        return msg
    if isinstance(msg, list):
        parts: list[str] = []
        for seg in msg:
            if not isinstance(seg, dict):
                continue
            seg_type = seg.get("type", "")
            seg_data = seg.get("data", {})
            if seg_type == "text":
                parts.append(seg_data.get("text", ""))
            elif seg_type == "image":
                # 包含图片 file MD5，确保不同图片产生不同 checksum
                parts.append(seg_data.get("file", ""))
            elif seg_type == "face":
                # 表情：用 face id
                parts.append(f"[face:{seg_data.get('id', '')}]")
            # forward / video / json 等其他类型跳过（嵌套转发 id 不固定）
        return "".join(parts)
    return ""


async def compute_checksum(event: GroupMessageEvent, bot: Bot) -> Optional[str]:
    """
    遍历消息 segments，计算内容 checksum。

    图片：取 file MD5 → "img:<md5>"（仅 subtype=0 外部图片，且消息中不含文字）
    视频：取 file MD5 → "vid:<md5>"
    JSON：取 data 字段 SHA256 → "json:<sha256>"
    转发：调用 get_forward_msg 取内容 → "fwd:<sha256>"
    其他：返回 None（不记录）
    """
    segments = list(event.get_message())
    has_text = any(seg.type == "text" for seg in segments)

    for seg in segments:
        logger.info(seg.type)
        if seg.type == "image":
            # 图片+文字 → 表情包用法，不记录
            if has_text:
                continue
            # 只记录外部发来的图片（subtype=0），忽略收藏表情（subtype=1）
            # 兼容不同适配器的大小写：subtype / subType
            subtype = str(
                seg.data.get("subtype")
                or seg.data.get("subType")
                or "0"
            )
            if subtype != "0":
                continue
            file_md5 = seg.data.get("file", "")
            if file_md5:
                return f"img:{file_md5}"

        elif seg.type == "video":
            file_md5 = seg.data.get("file", "")
            if file_md5:
                return f"vid:{file_md5}"

        elif seg.type == "json":
            json_data = seg.data.get("data", "")
            if json_data:
                sha = hashlib.sha256(json_data.encode("utf-8")).hexdigest()
                return f"json:{sha}"

        elif seg.type == "forward":
            forward_id = seg.data.get("id", "")
            logger.info(forward_id)
            if not forward_id:
                continue
            try:
                forward_data = await bot.get_forward_msg(id=forward_id)
                logger.info(forward_data)
                logger.info(type(forward_data))
                texts: list[str] = []

                # get_forward_msg 返回格式因适配器而异：dict 含 messages 字段，或直接是 list
                nodes: list = []
                if isinstance(forward_data, dict) and "messages" in forward_data:
                    nodes = forward_data["messages"]
                elif isinstance(forward_data, list):
                    nodes = forward_data

                for node in nodes:
                    if isinstance(node, dict):
                        texts.append(_extract_node_text(node))

                combined = "".join(texts)
                logger.info(combined)
                if combined:
                    sha = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                    return f"fwd:{sha}"
            except Exception as e:
                logger.warning(f"获取转发消息失败 (id={forward_id}): {e}")
                return None

    return None


# =============================================================================
# 图片发送
# =============================================================================

def get_image_for_group(group_id: int) -> str:
    """根据群号获取应发送的图片路径"""
    if group_id in config.per_group_image:
        return config.per_group_image[group_id]
    return config.echo_image_path


# =============================================================================
# 主 Handler
# =============================================================================

@echo.handle()
async def handle_content_echo(bot: Bot, event: GroupMessageEvent):
    group_id: int = event.group_id
    sender_id: int = event.user_id

    # 0. 检查开关状态
    if not await content_echo_redis.is_enabled(group_id):
        await echo.finish()

    # 1. 每条消息都递增计数器
    counter = await content_echo_redis.increment_counter(group_id)

    # 2. 计算 checksum（仅图片/视频/转发会返回非 None）
    checksum = await compute_checksum(event, bot)
    if checksum is None:
        # 不可记录类型的消息，仅计数后结束
        await echo.finish()

    logger.info(
        f"[content_echo] 记录 | 群:{group_id} | 发送者:{sender_id} | "
        f"计数:{counter} | checksum:{checksum}"
    )

    # 3. 查询是否已有相同 checksum 的记录
    existing = await content_echo_redis.get_record(group_id, checksum)

    if existing is not None:
        logger.info(
            f"[content_echo] 命中已有记录 | 群:{group_id} | checksum:{checksum[:40]}... | "
            f"上次计数:{existing['counter_value']} | 上次发送者:{existing.get('sender_id')} | "
            f"alerted:{existing.get('alerted', False)}"
        )
    else:
        logger.info(
            f"[content_echo] 新记录 | 群:{group_id} | checksum:{checksum[:40]}..."
        )

    # 4. 命中判断
    should_alert = False
    alerted_flag = False

    if existing is not None:
        diff = counter - existing["counter_value"]
        was_alerted = existing.get("alerted", False)

        if diff <= config.counter_threshold and not was_alerted:
            should_alert = True
            alerted_flag = True
        else:
            alerted_flag = was_alerted

    if should_alert:
        logger.info(
            f"🔁 content_echo 命中 | 群:{group_id} | "
            f"checksum:{checksum[:40]}... | "
            f"计数差:{diff} | 发送者:{sender_id}"
        )
        image_path = get_image_for_group(group_id)
        try:
            with open(image_path, "rb") as f:
                img_msg = MessageSegment.image(f.read())
            await bot.send_group_msg(group_id=group_id, message=img_msg)
        except Exception as e:
            logger.warning(f"发送 echo 图片失败 (群:{group_id}, 图:{image_path}): {e}")

    # 5. 写入/更新记录
    await content_echo_redis.set_record(
        group_id=group_id,
        checksum=checksum,
        data={
            "counter_value": counter,
            "timestamp": int(time.time() * 1000),
            "sender_id": sender_id,
            "alerted": alerted_flag,
        },
        ttl=config.record_ttl,
    )
    logger.info(
        f"[content_echo] 写入完成 | 群:{group_id} | checksum:{checksum[:40]}... | "
        f"计数:{counter} | alerted:{alerted_flag}"
    )

    await echo.finish()
