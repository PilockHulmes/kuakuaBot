
import json
import httpx

from nonebot import logger

url = "https://api.deepseek.com/chat/completions"
with open('./plugins/ask_deepseek/.deepseek_key', 'r') as f:
    api_key = f.read()

def generate_advanced_praise(target_id: str, chat_context: str) -> str:
    """
    改进版夸赞生成器，适配游戏+生活混合场景
    :param target_id: 需要夸赞的QQ号
    :param chat_context: 包含游戏与生活话题的聊天记录
    :return: 自然融合场景的夸赞语句
    """
    prompt = f"""你是一个活跃在多元化QQ群的成员，需要根据聊天内容得体自然地夸赞群友。请分析以下记录：
【聊天记录开始】
{chat_context}
【聊天记录结束】

【消息示例】
`[消息4] [用户28369507] [时间戳1740298092862]: 手都点麻了`
其中 [消息4] 是消息序号。[用户28369507] 是这则消息的发言人，用户两字后面的数字代表发言人qq号。[时间戳1740298092862]是这则消息的发送时间戳，格式为13位数字。最后则是消息的具体内容。

请为 [用户{target_id}] 生成夸赞消息，要求：
一、分析维度（根据实际内容选择最合适的1-2个方向）：
▶ 游戏向：
   - 战术策略/操作技巧
   - 新人指导/团队配合
   - 外观审美/道具收集
▶ 生活向：
   - 美食分享/烹饪技巧
   - 旅行见闻/摄影审美
   - 宠物照料/绿植养护
   - 情感支持/矛盾调解
   - 才艺展示(音乐/绘画等)
   - 日常工作
▶ 综合特质：
   - 幽默感/活跃氛围
   - 知识储备/学习能力
   - 细心体贴/善于观察

二、内容要求：
1. 必须结合最近几条相关发言内容
2. 使用年轻人流行用语但不过度玩梗
3. 若在发言中需要称呼发言人，请称呼其为喵呜呜、小猫或者群主
4. 避免重复近期已夸赞过的方向
5. 输出为单条消息，控制在15-30字
6. 若根据最近发言无法生成有趣的夸赞，那么生成空字符串即可
7. 若发言人说的话带抱怨的意思，或者情绪比较低落，那么不应该夸赞而是应该安慰

三、示例参考：
游戏场景："刚看了喵呜呜的走位教学，这蛇皮步比我本命英雄还流畅！"
生活场景："小猫拍的樱花雨构图绝了，是偷偷报了摄影班吧！"
综合场景："每次看群主调解矛盾都感觉在看职场剧，这情商慕了"

请生成针对[用户{target_id}]的夸赞："""
    return prompt

async def miaowu_kuakua(qq, history_messages):
    payload = {
    "model": "deepseek-chat",
    "messages": [
        {
            "role": "user",
            "content": generate_advanced_praise(qq, history_messages)
            }
        ],
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.request("POST", url, json=payload, headers=headers)
        
    if is_jsonable(response.text):    
        responseObj = json.loads(response.text)
        if "code" in responseObj:
            log.error(f"复读评分失败，错误原因：{responseObj['message']}")
            return responseObj['message']
    else:
        return "调用失败"

    kuakuaMessage = responseObj['choices'][0]['message']['content']
    logger.info(kuakuaMessage)
    return kuakuaMessage

def is_jsonable(x):
    try:
        json.loads(x)
        return True
    except:
        return False