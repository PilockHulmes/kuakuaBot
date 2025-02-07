import uuid
import asyncio
import json
import time

import websockets


async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def receive_messages(ws):
    while True:
        message = await ws.recv()
        print(f"收到消息: {message}" )
        parsedMessage = json.loads(message)
        if 'sub_type' in parsedMessage and parsedMessage['sub_type'] == 'normal' and parsedMessage['user_id'] == 392206976 and parsedMessage['message_type'] == 'group' and 'CQ:at,qq=2578188204' in parsedMessage['raw_message'] and '夸夸' in parsedMessage['message'][1]['data']['text']:
            print('goes here')
            echo = str(uuid.uuid4())
            data = {
                "action": "send_group_msg",
                "params": {
                    "group_id": parsedMessage['group_id'],
                    "message": {
                        "type": "text",
                        "data": {
                            "text": "以后这里会替换成用 deepseek 产出的随机夸喵台词"
                        }
                    }
                },
                'echo': echo
            }
            await ws.send(json.dumps(data))


async def main():
    uri = "ws://localhost:3001"  # 替换为你的 LLOneBot WebSocket 正向地址
    group_id = 853041949
    
    async with websockets.connect(uri) as websocket:
        asyncio.create_task(receive_messages(websocket))
        while True:
            time.sleep(1)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input, "输入消息内容: ")
        # while True:
        #     message = await async_input("输入消息内容: ")
        #     echo = str(uuid.uuid4())
        #     data = {
        #         "action": "send_group_msg",
        #         "params": {
        #             "group_id": group_id,
        #             "message": {
        #                 "type": "text",
        #                 "data": {
        #                     "text": message
        #                 }
        #             }
        #         },
        #         'echo': echo
        #     }
        #     await websocket.send(json.dumps(data))

asyncio.run(main())