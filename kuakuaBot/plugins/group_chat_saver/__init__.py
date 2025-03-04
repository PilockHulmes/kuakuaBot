from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import on_message

from .config import Config
from .redis.chatsaver import chat_saver

__plugin_meta__ = PluginMetadata(
    name="group_chat_saver",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [853041949, 1020882307, 244960293]
async def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

record = on_message(priority=10, rule=group_in_whitelist, block=False)

@record.handle()
async def handle(event: GroupMessageEvent):
    if event.get_message().extract_plain_text() == "":
        await record.finish()
    await chat_saver.storeMessage(event.group_id, event.user_id, event.get_message().extract_plain_text(), event.message_type)
    await record.finish()