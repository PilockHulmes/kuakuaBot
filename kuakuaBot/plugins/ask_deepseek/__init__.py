from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot import logger
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.rule import Rule


# from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent

from .config import Config
from .prompt import send_message_v3_group, send_message_r1, send_message_v3_private


__plugin_meta__ = PluginMetadata(
    name="ask_deepseek",
    description="a simple plugin that integrates openai api and deepseek key for asking questions",
    usage="@robotname 那我问你 xxxx",
    config=Config,
)

config = get_plugin_config(Config)

whiltelist = [853041949, 1020882307, 244960293]
def group_in_whitelist(event: Event):
    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
        return int(group_id) in whiltelist
    return False

ask = on_message(rule=Rule(group_in_whitelist) & to_me(), priority=10)

@ask.handle()
async def handle_function(event: GroupMessageEvent):
    if question := event.get_message():
        logger.info(question)
        answer = await send_message_v3_group(question)
        logger.info(answer)
        await ask.finish(answer)

@ask.handle()
async def handle_function(event: PrivateMessageEvent):
    if question := event.get_message():
        logger.info(question)
        await ask.send("收到问题，正在问 deepseek")
#         answer, resason = await send_message_r1(event.get_user_id(), question)
#         if resason is None:
#             await ask.finish(f"请求出错，请重试。错误信息为: {answer}")
#         await ask.send(f"""以下是思考过程：
# {resason}""")

        answer = await send_message_v3_private(event.get_user_id(), question)
        
        await ask.finish(answer)