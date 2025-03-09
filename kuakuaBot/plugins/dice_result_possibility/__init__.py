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

@dice_rate.handle()
async def handle(event: GroupMessageEvent, args: Message = CommandArg()):
    input_str = args.extract_plain_text()
    try:
        n, d, modifier, operator, target = parse_input(input_str)
        if n < 1 or d < 1:
            await dice_rate.finish("骰子数量以及每个骰子面数只少要是 1")
        probability = calculate_probability(n, d, modifier, operator, target)
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

def compute_dice_sums(n, d):
    current_sums = defaultdict(int)
    current_sums[0] = 1
    for _ in range(n):
        next_sums = defaultdict(int)
        for s in current_sums:
            for face in range(1, d + 1):
                next_sums[s + face] += current_sums[s]
        current_sums = next_sums
    return current_sums

def compare(value, operator, target):
    ops = {
        '>=': lambda v, t: v >= t,
        '>': lambda v, t: v > t,
        '<=': lambda v, t: v <= t,
        '<': lambda v, t: v < t,
        '==': lambda v, t: v == t,
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