
import json
import httpx

from nonebot import logger

url = "https://api.siliconflow.cn/v1/chat/completions"
with open('./plugins/ask_deepseek/.deepseek_key', 'r') as f:
    api_key = f.read()


async def send_message_v3_group(message):
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {
                "role": "user",
                "content": f"""请问:
{message}

请用纯文本格式返回，并且尽量把回复内容压缩到100字内，最多不超过200字。
"""
            }
        ],
        "stream": False,
        "max_tokens": 200,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
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
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": asking,
        "stream": False,
        "max_tokens": 4096,
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
        "model": "deepseek-ai/DeepSeek-R1",
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