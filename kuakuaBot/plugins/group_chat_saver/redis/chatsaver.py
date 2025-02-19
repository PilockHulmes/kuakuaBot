from redis.asyncio import Redis

class ChatSaver:
    def __init__(self):
        self.redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    
    
    def __del__(self):
        self.redis.close()