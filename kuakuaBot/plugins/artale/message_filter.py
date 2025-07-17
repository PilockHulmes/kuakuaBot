from redis.asyncio import Redis
import hashlib
import time

USER_KEYWORDS = "user_keywords"
PROCESSED_MESSAGES = "processed_messages"
PAUSE_NOTIFICATION = "pause_notification"

class MessageFilter:
    def __init__(self):
        self.redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    async def pause_user(self, group_id, user_id):
        """用户暂停功能"""
        await self.redis.set(f'{PAUSE_NOTIFICATION}:{group_id}:{user_id}', 1)
    
    async def active_user(self, group_id, user_id):
        """用户启用功能"""
        await self.redis.delete(f'{PAUSE_NOTIFICATION}:{group_id}:{user_id}')
    
    async def is_user_active(self, group_id, user_id):
        """检查用户是否启用功能"""
        exists = await self.redis.exists(f'{PAUSE_NOTIFICATION}:{group_id}:{user_id}')
        return exists == 0

    async def add_user_keyword(self, group_id, user_id, keyword):
        """添加用户关键字"""
        await self.redis.hset(f'{USER_KEYWORDS}:{group_id}:{user_id}', keyword, 1)
    
    async def remove_user_keyword(self, group_id, user_id, keyword):
        """删除用户关键字"""
        await self.redis.hdel(f'{USER_KEYWORDS}:{group_id}:{user_id}', keyword)
    
    async def clear_user_keywords(self, group_id, user_id):
        """清空用户关键字"""
        await self.redis.delete(f'{USER_KEYWORDS}:{group_id}:{user_id}')
    
    async def get_user_keywords(self, group_id, user_id):
        """获取用户关键字列表"""
        return await self.redis.hkeys(f'{USER_KEYWORDS}:{group_id}:{user_id}')
    
    async def is_message_processed(self, message):
        """检查消息是否已处理"""
        msg_hash = hashlib.md5(message.encode()).hexdigest()
        return await self.redis.zscore(f'{PROCESSED_MESSAGES}', msg_hash) is not None
    
    async def add_message_processed(self, message):
        """存储消息哈希用于去重"""
        msg_hash = hashlib.md5(message.encode()).hexdigest()
        # 使用当前时间戳作为分数
        timestamp = time.time()
        
        # 使用事务确保原子性
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zadd(f'{PROCESSED_MESSAGES}', {msg_hash: timestamp})
            # 保持集合大小不超过max_length
            pipe.zremrangebyrank(f'{PROCESSED_MESSAGES}', 0, -50 - 1)
            await pipe.execute()

    async def process_message(self, group_id, message):
        """处理新消息并返回匹配的用户"""
        # 查找所有用户并检查关键字匹配
        matched_users = []
        async for user_key in self.redis.scan_iter(match=f'{USER_KEYWORDS}:{group_id}:*'):
            user_id = user_key.split(':')[2]
            active = await self.is_user_active(group_id, user_id)
            if not active:
                continue
            keywords = await self.get_user_keywords(group_id, user_id)
            if any(keyword.lower() in message.lower() for keyword in keywords):
                matched_users.append(user_id)
        
        return matched_users