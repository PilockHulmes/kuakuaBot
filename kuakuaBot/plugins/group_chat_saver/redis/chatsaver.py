from redis.asyncio import Redis
import time
import json

class ChatSaver():
    def __init__(self):
        self.redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    async def addQQ(self, group_id, qq, title = "saved_id"): 
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.hset(
                name=f"qq_group:{group_id}:{title}",
                key=qq,
                value=""
            )
            await pipe.execute()

    async def addQQs(self, group_id, qqs, title = "saved_id"):
        async with self.redis.pipeline(transaction=True) as pipe:
            for qq in qqs:
                await pipe.hset(
                    name=f"qq_group:{group_id}:{title}",
                    key=qq,
                    value=""
                )
            await pipe.execute()
    
    async def removeQQ(self, group_id, qq, title= "saved_id"):
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.hdel(f"qq_group:{group_id}:{title}", qq)
            await pipe.execute()

    async def hasQQ(self, group_id, qq, title = "saved_id"):
        return await self.redis.hexists(
            name=f"qq_group:{group_id}:{title}",
            key=qq
        )
    
    async def listQQ(self, group_id, title = "saved_id"):
        keys = await self.redis.hkeys(f"qq_group:{group_id}:{title}")
        return [int(qq) for qq in keys]

    async def saveQQInfo(self, group_id, qq, info, title = "saved_id"):
        await self.redis.hset(
            name=f"qq_group:{group_id}:{title}:info",
            key=qq,
            value=info
        )
    
    async def getQQInfo(self, group_id, qq, title = "saved_id"):
        return await self.redis.hget(
            name=f"qq_group:{group_id}:{title}:info",
            key=qq,
        )

    async def storeMessage(self, group_id, sender_id, content, message_type="text"):
        # 生成唯一消息ID
        timestamp = int(time.time() * 1000)
        msg_id = f"{timestamp}_{group_id}_{sender_id}_{hash(content) % 10000}"
        
        # 构建消息对象
        message = {
            "msg_id": msg_id,
            "group_id": group_id,
            "sender_id": sender_id,
            "content": content,
            "timestamp": timestamp,
            "message_type": message_type
        }
        
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.hset(
                name=f"qq_group:{group_id}:msg_data",
                key=msg_id,
                value=json.dumps(message)
            )
            await pipe.zadd(
                name=f"qq_group:{group_id}:timeline",
                mapping={msg_id: timestamp}
            )
            await pipe.execute()
    
    async def getLatestMessagesForRepeater(self, group_id, message_count = 10, duration_in_secods = 300):
        end_timestamp = int(time.time() * 1000)
        start_timestamp = int(time.time() * 1000) - duration_in_secods * 1000
        msg_ids = await self.redis.zrangebyscore(
            name=f"qq_group:{group_id}:timeline",
            min=start_timestamp,
            max=end_timestamp,
        )
        async with self.redis.pipeline(transaction=True) as pipe:
            for msg_id in msg_ids[-message_count:]:
                pipe.hget(f"qq_group:{group_id}:msg_data", msg_id)
            msgs = await pipe.execute()
        return [json.loads(msg) for msg in msgs]
    
    def __del__(self):
        self.redis.close()
        
chat_saver = ChatSaver()