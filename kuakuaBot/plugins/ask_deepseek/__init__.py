from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot import logger
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg


from nonebot.adapters.onebot.v11 import MessageEvent

from .config import Config
from .prompt import send_message
from .utils import whitelist_groups

__plugin_meta__ = PluginMetadata(
    name="ask_deepseek",
    description="a simple plugin that integrates openai api and deepseek key for asking questions",
    usage="@robotname 那我问你 xxxx",
    config=Config,
)

config = get_plugin_config(Config)

ask = on_message(rule=to_me(), priority=10)

@ask.handle()
async def handle_function(event: MessageEvent):
    if question := event.get_message():
        logger.info(question)
        answer = await send_message(question)
        logger.info(answer)
        await ask.finish(answer)