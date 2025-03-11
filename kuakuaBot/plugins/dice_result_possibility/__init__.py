from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot import logger, on_command, on_regex, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from redis.asyncio import Redis
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.rule import Rule
from nonebot.params import CommandArg
from nonebot.adapters import Message

import re
from collections import defaultdict

__plugin_meta__ = PluginMetadata(
    name="dice_result_possibility",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [
    244960293,
    1020882307,
]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

dice_rate = on_command("dice", aliases=set(["骰子"]), priority=15, block=True, rule=Rule(group_in_whitelist))
dice_att_rate = on_command("diceatt", aliases=set(["攻击骰子"]), priority=15, block=True, rule=Rule(group_in_whitelist))

@dice_rate.handle()
async def handle(event: GroupMessageEvent, args: Message = CommandArg()):
    input_str = args.extract_plain_text()
    try:
        n, d, modifier, operator, target = parse_input(input_str)
        if n < 1 or d < 1:
            await dice_rate.finish("骰子数量以及每个骰子面数至少要是 1")
        probability = calculate_probability(n, d, modifier, operator, target)
        await dice_rate.finish(f"概率是 {probability:.4f} ({probability*100:.2f}%)")
    except ValueError as e:
        await dice_rate.finish(f"报错了: {e}")

@dice_att_rate.handle()
async def handle(event: GroupMessageEvent, args: Message = CommandArg()):
    input_str = args.extract_plain_text()
    try:
        (left_parts, operator, right_parts) = parse_dice_inequality(input_str)

        probability = calculate_complex_probability(left_parts, operator, right_parts)
        await dice_rate.finish(f"概率是 {probability:.4f} ({probability*100:.2f}%)")
    except ValueError as e:
        await dice_rate.finish(f"报错了: {e}")

def parse_input(input_str):
    input_str = input_str.replace(' ', '').lower()

    match = re.match(r'^(.+?)(>=|<=|>|<|==|!=)(\d+)$', input_str)
    if not match:
        raise ValueError("Invalid input format")
    dice_expr, operator, target = match.groups()
    target = int(target)
    
    dice_match = re.match(r'^(\d+)d(\d+)([+-]\d+)?$', dice_expr)
    if not dice_match:
        raise ValueError("Invalid dice expression")
    n, d = int(dice_match.group(1)), int(dice_match.group(2))
    modifier = int(dice_match.group(3)) if dice_match.group(3) else 0
    
    return n, d, modifier, operator, target


def parse_expression(expr):
    # 匹配项的正则表达式，允许骰子或数字，可能有符号
    matches = re.findall(r'([+-]?)(\d+[dD]\d+|\d+)', expr, flags=re.IGNORECASE)
    parsed = []
    for sign, part in matches:
        if not sign:
            sign = '+'  # 默认符号为+
        # 将骰子中的d统一转为小写，以便后续操作
        part_upper = part.lower()
        parsed.append(f"{sign}{part_upper}")
    return parsed

def parse_dice_inequality(s):
    s = s.replace(' ', '').lower()
    logger.info(s)
    # 分割比较运算符
    operator_pattern = r'(>=|<=|==|>|<|=|!=)'
    parts = re.split(operator_pattern, s)
    if len(parts) != 3:
        raise ValueError("无效的不等式表达式")
    left_expr, operator, right_expr = parts

    # 解析左右表达式
    left_parts = parse_expression(left_expr)
    right_parts = parse_expression(right_expr)
    print(left_parts,operator,right_parts)
    return (left_parts, operator, right_parts)

def move_side(part):
    return part.translate(str.maketrans("+-", "-+"))

def sum_nums(nums):
    s = 0
    for num in nums:
        s += int(num)
    return s

def merge_two_sums(sum1, sum2):
    merged_sums = defaultdict(int)
    for face1 in sum1:
        for face2 in sum2:
            merged_sums[face1 + face2] += sum1[face1] * sum2[face2]
    return merged_sums

def compute_dice_sums(n, d, is_minus = False):
    current_sums = defaultdict(int)
    current_sums[0] = 1
    for _ in range(n):
        next_sums = defaultdict(int)
        for s in current_sums:
            for face in range(1, d + 1):
                next_sums[s + face] += current_sums[s]
        current_sums = next_sums
    if is_minus:
        new_result = defaultdict(int)
        for key in current_sums:
            new_result[-key] = current_sums[key]
        return new_result
    return current_sums

def compare(value, operator, target):
    ops = {
        '>=': lambda v, t: v >= t,
        '>': lambda v, t: v > t,
        '<=': lambda v, t: v <= t,
        '<': lambda v, t: v < t,
        '==': lambda v, t: v == t,
        '=': lambda v, t: v == t,
        '!=': lambda v, t: v != t,
    }
    return ops[operator](value, target)

def calculate_probability(n, d, modifier, operator, target):
    sum_counts = compute_dice_sums(n, d)
    total = sum(sum_counts.values())
    
    adjusted_counts = defaultdict(int)
    for s, count in sum_counts.items():
        adjusted_s = s + modifier
        adjusted_counts[adjusted_s] += count
    
    condition_met = 0
    for s, count in adjusted_counts.items():
        if compare(s, operator, target):
            condition_met += count
    
    return condition_met / total

dice_regex = r"^([+-])(\d+)d(\d+)$"
def calculate_complex_probability(left, operator, right):
    left_dices = []
    right_digits = []
    for item in left:
        if "d" in item:
            left_dices.append(item)
        else:
            right_digits.append(move_side(item))
    for item in right:
        if "d" in item:
            left_dices.append(move_side(item))
        else:
            right_digits.append(item)
    print(left_dices, right_digits)
    total_sum = defaultdict(int)
    total_sum[0] = 1
    for dice in left_dices:
        dice_match = re.match(dice_regex, dice)
        if not dice_match:
            raise ValueError("Invalid dice expression")
        symbol = dice_match.group(1)
        n, d = int(dice_match.group(2)), int(dice_match.group(3))
        current_sum = compute_dice_sums(n, d, symbol == "-")
        print("current", current_sum)
        total_sum = merge_two_sums(total_sum, current_sum)
        print("total", total_sum)

    target = sum_nums(right_digits)
    
    condition_met = 0
    total_conditions = sum(total_sum.values())
    for sides, count in total_sum.items():
        if compare(sides, operator, target):
            condition_met += count
    return condition_met/total_conditions