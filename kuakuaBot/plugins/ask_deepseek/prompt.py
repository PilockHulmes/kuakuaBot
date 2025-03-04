
import json
import httpx

from nonebot import logger

url = "https://api.deepseek.com/chat/completions"
with open('./plugins/ask_deepseek/.deepseek_key', 'r') as f:
    api_key = f.read()


async def send_message_v3_group(message):
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": f"""请问:
{message}

请用纯文本格式返回，并且尽量把回复内容压缩到100字内，最多不超过200字。
"""
            }
        ],
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.request("POST", url, json=payload, headers=headers)
    logger.info(type(response.text))
    logger.info(response.text)
    responseObj = json.loads(response.text)
    if "code" in responseObj:
        return responseObj['message']
    return responseObj['choices'][0]['message']['content']

message_history_v3 = {}
async def send_message_v3_private(qq_number, message, new_thread = False):
    if qq_number not in message_history_v3 or new_thread:
        message_history_v3[qq_number] = []
    history_message = message_history_v3[qq_number]
    current_user_message = {
        "role": "user",
        "content": f"{message}"
    }
    asking = history_message + [current_user_message]
    payload = {
        "model": "deepseek-chat",
        "messages": asking,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=500) as client:
        response = await client.request("POST", url, json=payload, headers=headers)
    logger.info(type(response.text))
    logger.info(response.text)
    responseObj = json.loads(response.text)
    if "code" in responseObj:
        # do not store history since failed to answer
        return responseObj['message']
    message_history_v3[qq_number].append(current_user_message)
    message_history_v3[qq_number].append({
        "role": "assistant",
        "content": responseObj['choices'][0]['message']['content']
    })
    return responseObj['choices'][0]['message']['content']


message_history_r1 = {}
async def send_message_r1(qq_number, message, new_thread = False):
    if qq_number not in message_history_r1 or new_thread:
        message_history_r1[qq_number] = []
    history_message = message_history_r1[qq_number]
    current_user_message = {
        "role": "user",
        "content": f"{message}"
    }
    asking = history_message + [current_user_message]
    payload = {
        "model": "deepseek-reasoner",
        "messages": asking,
        "stream": False,
        "max_tokens": 8192,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0,
        "n": 1,
        "response_format": {"type": "text"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=500) as client:
        response = await client.request("POST", url, json=payload, headers=headers)
    logger.info(type(response.text))
    logger.info(response.text)
    responseObj = json.loads(response.text)
    if "code" in responseObj:
        # do not store history since failed to answer
        return responseObj['message'], None
    message_history_r1[qq_number].append(current_user_message)
    message_history_r1[qq_number].append({
        "role": "assistant",
        "content": responseObj['choices'][0]['message']['content']
    })
    return (responseObj['choices'][0]['message']['content'], responseObj['choices'][0]['message']['reasoning_content'])

async def send_repeater_messages_v3(messages):

    payload = {
    "model": "deepseek-chat",
    "messages": [
        {
            "role": "user",
            "content": """
你是一个QQ群聊消息分析专家，请按以下步骤评估最新消息的复读潜力：

**消息记录**（按时间早晚顺序排列，最新消息在最后）：
[[messages]]

**消息记录示例**
`[消息4] [用户28369507] [时间戳1740298092862]: 手都点麻了`
其中 [消息4] 是消息序号。[用户28369507] 是这则消息的发言人，用户两字后面的数字代表发言人qq号。[时间戳1740298092862]是这则消息的发送时间戳，格式为13位数字。最后则是消息的具体内容。

**任务要求**：

按照一下四个步骤来分析每一条消息，并最终给出百分制的评分：
1. 分析消息的趣味性，趣味越高评分越高，趣味性包括但不限于：
    - 是否包含热梗词/流行语？
    - 基于上下文关联性对消息幽默感评分
2. 队形潜力判断，队形越多评分越高：
    - 统计相同/相似内容在最近几条消息中的重复次数
    - 判断是否已形成可延续的队形模式
    - 若相同/相似内容在最近几条消息中重复次数比较高，说明已经形成队形，需要增加评分
3. 风险性筛查，若包含风险则给 0 分：
    - 检查是否包含敏感词（列表：代购/政治/广告）
    - 分析可能引发的负面情绪（如焦虑/争吵）
4. 时间衰减计算，越早的消息评分越低

**输出格式**：
{
  "消息0": "(评分) (说明原因)",
  "消息1": "(评分) (说明原因)",
  "消息2": "(评分) (说明原因)",
  "消息3": "(评分) (说明原因)",
  "消息4": "(评分) (说明原因)",
  ... (对所有消息都给出评分与原因)
}

请确保你输出的是一个完整格式的 json 字符串
""".replace('[[messages]]', messages)
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
    logger.info(type(response.text))
    logger.info(response.text)    
    
    if is_jsonable(response.text):    
        responseObj = json.loads(response.text)
        if "code" in responseObj:
            log.error(f"复读评分失败，错误原因：{responseObj['message']}")
            return responseObj['message']
    else:
        return "调用失败"
    jsonStr = responseObj['choices'][0]['message']['content'].removeprefix("```json").removesuffix("```")
    logger.info(messages)
    explain = json.loads(jsonStr)
    logger.info(json.dumps(explain, indent=4, ensure_ascii=False))
    return explain

def is_jsonable(x):
    try:
        json.loads(x)
        return True
    except:
        return False