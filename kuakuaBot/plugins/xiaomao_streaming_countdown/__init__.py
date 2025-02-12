from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot.rule import to_me

from .config import Config

from datetime import date, datetime

__plugin_meta__ = PluginMetadata(
    name="xiaomao_streaming_countdown",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [853041949, 1020882307]
async def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False


streaming_start_date = datetime.strptime("2052-01-01", "%Y-%m-%d")
start = on_command("开播倒计时", aliases={"群主什么时候直播", "小猫什么时候直播"}, priority=10, block=True, rule=group_in_whitelist)

@start.handle()
async def handle_function():
    delta = streaming_start_date - datetime.now()
    
    # d = streaming_start_date.strftime("%Y-%m-%d")
    await start.finish(f"距离开播({streaming_start_date})还有 {delta.days} 天")
