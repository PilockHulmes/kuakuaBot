
import json
import httpx

from nonebot import logger

url = "https://api.siliconflow.cn/v1/chat/completions"
with open('./plugins/ask_deepseek/.deepseek_key', 'r') as f:
    api_key = f.read()


async def send_message_v3(message):
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {
                "role": "user",
                "content": f"""{message}"""
            }
        ],
        "stream": False,
        "max_tokens": 4096,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
        # "tools": [
        #     {
        #         "type": "function",
        #         "function": {
        #             "description": "<string>",
        #             "name": "<string>",
        #             "parameters": {},
        #             "strict": False
        #         }
        #     }
        # ]
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

async def send_message_r1(message):
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": f"{message}"
            }
        ],
        "stream": False,
        "max_tokens": 8192,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0,
        "n": 1,
        "response_format": {"type": "text"},
        # "tools": [
        #     {
        #         "type": "function",
        #         "function": {
        #             "description": "<string>",
        #             "name": "<string>",
        #             "parameters": {},
        #             "strict": False
        #         }
        #     }
        # ]
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
        return responseObj['message'], None
    return (responseObj['choices'][0]['message']['content'], responseObj['choices'][0]['message']['reasoning_content'])