"""
塔罗牌占卜插件 - NoneBot 2 插件

命令：
- /塔罗 <问题>          → 默认三张牌阵占卜
- /塔罗 <牌阵> <问题>   → 指定牌阵占卜
- /tarot 同 /塔罗
"""

from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import logger

from .config import Config
from .tarot_deck import (
    VALID_SPREADS,
    DEFAULT_SPREAD,
    TOPIC_MIN_LENGTH,
    TOPIC_MAX_LENGTH,
    sanitize_input_text,
    contains_blocked_keyword,
    detect_prompt_injection,
    parse_command_args,
    draw_cards,
    build_tarot_prompt,
    call_deepseek_tarot,
)

__plugin_meta__ = PluginMetadata(
    name="tarot",
    description="塔罗牌占卜插件 - 随机抽牌，AI 解读",
    usage="发送 /塔罗 <问题> 进行占卜，/塔罗 <牌阵> <问题> 指定牌阵",
    config=Config,
)

config = get_plugin_config(Config)

# =============================================================================
# 群白名单
# =============================================================================

whitelist = [853041949, 1020882307, 244960293]


def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whitelist
    return False


# =============================================================================
# 命令注册
# =============================================================================

tarot = on_command(
    "塔罗",
    aliases={"tarot"},
    priority=15,
    block=True,
    rule=Rule(group_in_whitelist),
)


@tarot.handle()
async def handle_tarot(event: GroupMessageEvent, args: Message = CommandArg()):
    raw_text = args.extract_plain_text().strip()

    # Step 1: 解析参数
    spread, topic = parse_command_args(raw_text)

    if spread is None:
        spread = DEFAULT_SPREAD

    # Step 2: 校验 topic
    if topic is None or len(topic) < TOPIC_MIN_LENGTH:
        valid_spreads_str = "、".join(sorted(VALID_SPREADS))
        await tarot.finish(
            f"🔮 塔罗牌占卜\n\n"
            f"用法：\n"
            f"  /塔罗 <问题>          → 默认三张牌阵\n"
            f"  /塔罗 <牌阵> <问题>   → 指定牌阵\n\n"
            f"问题至少 {TOPIC_MIN_LENGTH} 个字符，最多 {TOPIC_MAX_LENGTH} 个字符。\n"
            f"支持的牌阵：{valid_spreads_str}"
        )

    if len(topic) > TOPIC_MAX_LENGTH:
        await tarot.finish(f"问题过长，请控制在 {TOPIC_MAX_LENGTH} 字以内。")

    # Step 3: 安全过滤
    if contains_blocked_keyword(topic) or detect_prompt_injection(topic):
        logger.warning(f"塔罗占卜安全过滤触发 | 群:{event.group_id} | 用户:{event.user_id}")
        await tarot.finish("请求内容包含不允许的内容，请修改后重试。")

    # Step 4: 校验牌阵
    if spread not in VALID_SPREADS:
        valid_spreads_str = "、".join(sorted(VALID_SPREADS))
        await tarot.finish(f"不支持的牌阵「{spread}」。支持的牌阵：{valid_spreads_str}")

    logger.info(f"🔮 塔罗占卜 | 群:{event.group_id} | 用户:{event.user_id} | 牌阵:{spread} | 主题:{topic[:30]}")

    # Step 5: 随机抽牌
    cards = draw_cards(spread)

    # 格式化抽牌结果
    card_display = "\n".join(
        f"  {i+1}. {c['name']}（{c['orientation']}）"
        for i, c in enumerate(cards)
    )
    await tarot.send(f"🔮 正在为「{topic}」占卜...\n\n【抽到的牌】\n{card_display}")

    # Step 6: 构建 prompt 并调用 AI
    prompt = build_tarot_prompt(topic, spread, cards)
    result = await call_deepseek_tarot(prompt)

    # Step 7: 返回结果
    await tarot.finish(f"🔮 塔罗解读结果：\n\n{result}")
