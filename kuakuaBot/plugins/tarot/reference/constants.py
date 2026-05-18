# constants.py
# 塔罗牌API合法值白名单配置
# 标准韦特塔罗牌（Rider-Waite）78张牌 + 常用牌阵/位置定义

# =============================================================================
# 塔罗牌名称白名单（78张标准牌）
# =============================================================================

# 大阿卡纳（Major Arcana）- 22张
MAJOR_ARCANA = [
    "愚人", "魔术师", "女祭司", "皇后", "皇帝", "教皇", "恋人", "战车",
    "力量", "隐士", "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔",
    "塔", "星星", "月亮", "太阳", "审判", "世界"
]

# 小阿卡纳（Minor Arcana）- 56张，按花色分组
# 权杖组（Wands）- 火元素：行动、创造、热情
WANDS = [
    "权杖Ace", "权杖二", "权杖三", "权杖四", "权杖五", 
    "权杖六", "权杖七", "权杖八", "权杖九", "权杖十",
    "权杖侍从", "权杖骑士", "权杖王后", "权杖国王"
]

# 圣杯组（Cups）- 水元素：情感、关系、直觉
CUPS = [
    "圣杯Ace", "圣杯二", "圣杯三", "圣杯四", "圣杯五", 
    "圣杯六", "圣杯七", "圣杯八", "圣杯九", "圣杯十",
    "圣杯侍从", "圣杯骑士", "圣杯王后", "圣杯国王"
]

# 宝剑组（Swords）- 风元素：思维、冲突、决策
SWORDS = [
    "宝剑Ace", "宝剑二", "宝剑三", "宝剑四", "宝剑五", 
    "宝剑六", "宝剑七", "宝剑八", "宝剑九", "宝剑十",
    "宝剑侍从", "宝剑骑士", "宝剑王后", "宝剑国王"
]

# 星币组（Pentacles）- 土元素：物质、财富、现实
PENTACLES = [
    "星币Ace", "星币二", "星币三", "星币四", "星币五", 
    "星币六", "星币七", "星币八", "星币九", "星币十",
    "星币侍从", "星币骑士", "星币王后", "星币国王"
]

# 完整小阿卡纳列表
MINOR_ARCANA = WANDS + CUPS + SWORDS + PENTACLES

# 所有合法牌名集合（用于快速校验）
VALID_CARDS_SET = set(MAJOR_ARCANA + MINOR_ARCANA)

# 按分类组织的完整字典（兼容原有结构）
VALID_CARDS = {
    "大阿卡纳": MAJOR_ARCANA,
    "小阿卡纳": MINOR_ARCANA,
    "权杖": WANDS,
    "圣杯": CUPS,
    "宝剑": SWORDS,
    "星币": PENTACLES,
    "全部": list(VALID_CARDS_SET)  # 78张完整列表
}


# =============================================================================
# 合法牌阵名称（Spread）
# =============================================================================
VALID_SPREADS = {
    "单张",
    "三张牌阵",
    "圣三角牌阵",
    "四元素牌阵",
    "钻石牌阵",
    "二择一牌阵",
    "十字牌阵",
    "五芒星牌阵",
    "六芒星牌阵",
    "吉普赛十字法"
}

# 各牌阵对应的建议牌数（用于校验）
SPREAD_CARD_LIMITS = {
    "三张牌阵": (3, 3),
    "圣三角牌阵": (3, 3),
    "四元素牌阵": (4, 4),
    "钻石牌阵": (4, 4),
    "二择一牌阵": (5, 5),
    "十字牌阵": (5, 5),
    "五芒星牌阵": (5, 5),
    "六芒星牌阵": (6, 6),
    "吉普赛十字法": (5, 5)
}

# =============================================================================
# 安全过滤配置
# =============================================================================

# 请求内容黑名单关键词（防Prompt注入/滥用）
BLOCKED_KEYWORDS = [
    # 系统指令覆盖尝试
    "system prompt", "ignore instructions", "override system",
    "you are now", "act as", "角色扮演", "切换身份",
    # 代码/数据泄露尝试  
    "output json only", "return raw", "base64 encode",
    "eval(", "exec(", "import os", "import sys",
    # 敏感内容
    "政治", "暴力", "色情", "赌博", "诈骗", "违法",
    # 特殊符号注入
    "<<<", ">>>", "{{", "}}", "```python", "```json"
]

# 咨询主题长度限制
TOPIC_MIN_LENGTH = 3
TOPIC_MAX_LENGTH = 200

# 单次请求最大牌数（防资源滥用）
MAX_CARDS_PER_REQUEST = 12

# =============================================================================
# 辅助验证函数
# =============================================================================

def is_valid_card(card_name: str) -> bool:
    """检查牌名是否合法"""
    return card_name in VALID_CARDS_SET

def get_card_category(card_name: str) -> str | None:
    """返回牌所属类别（大/小阿卡纳+花色）"""
    if card_name in MAJOR_ARCANA:
        return "大阿卡纳"
    if card_name in WANDS:
        return "权杖"
    if card_name in CUPS:
        return "圣杯"
    if card_name in SWORDS:
        return "宝剑"
    if card_name in PENTACLES:
        return "星币"
    return None

def validate_spread_card_count(spread: str, card_count: int) -> tuple[bool, str]:
    """验证牌阵与牌数是否匹配"""
    if spread not in VALID_SPREADS:
        return False, f"不支持的牌阵: {spread}"
    
    limits = SPREAD_CARD_LIMITS.get(spread, (1, MAX_CARDS_PER_REQUEST))
    min_cards, max_cards = limits
    
    if not (min_cards <= card_count <= max_cards):
        return False, f"{spread} 需要 {min_cards}-{max_cards} 张牌，当前: {card_count}"
    
    return True, "OK"

def sanitize_input_text(text: str) -> str:
    """基础文本清洗：去除首尾空格+控制字符"""
    if not text:
        return ""
    # 移除不可见控制字符（保留中文标点和换行）
    cleaned = "".join(c for c in text if c.isprintable() or c in '\n\r\t')
    return cleaned.strip()

def contains_blocked_keyword(text: str) -> bool:
    """检查文本是否包含黑名单关键词"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in BLOCKED_KEYWORDS)