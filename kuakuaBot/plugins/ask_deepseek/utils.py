from nonebot import get_plugin_config
from nonebot.adapters import Event
from nonebot import logger

from .config import Config

config = get_plugin_config(Config)

async def whitelist_groups(event: Event):
    logger.info(event.get_session_id())
    return True