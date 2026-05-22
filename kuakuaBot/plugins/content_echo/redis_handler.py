import json
from typing import Optional
from redis.asyncio import Redis


class ContentEchoRedis:
    """content_echo 插件的 Redis 操作封装"""

    def __init__(self):
        self.redis = Redis.from_url(
            "redis://localhost:6379/0", decode_responses=True
        )

    # ------------------------------------------------------------------
    # 消息计数器（每个群独立，每条消息 +1，无论是否被记录）
    # ------------------------------------------------------------------

    async def increment_counter(self, group_id: int) -> int:
        """递增群消息计数器并返回新值"""
        return await self.redis.incr(f"qq_group:{group_id}:echo_counter")

    # ------------------------------------------------------------------
    # 内容记录（独立 key，天然支持 TTL）
    # ------------------------------------------------------------------

    async def get_record(
        self, group_id: int, checksum: str
    ) -> Optional[dict]:
        """查询指定 checksum 的记录，不存在返回 None"""
        data = await self.redis.get(
            f"qq_group:{group_id}:echo:{checksum}"
        )
        if data is None:
            return None
        return json.loads(data)

    async def set_record(
        self,
        group_id: int,
        checksum: str,
        data: dict,
        ttl: int = 86400,
    ) -> None:
        """写入/覆盖记录，设置 TTL"""
        await self.redis.setex(
            f"qq_group:{group_id}:echo:{checksum}",
            ttl,
            json.dumps(data),
        )

    def __del__(self):
        self.redis.close()

    # ------------------------------------------------------------------
    # 开关状态（按群独立，持久化到 Redis）
    # ------------------------------------------------------------------

    async def is_enabled(self, group_id: int) -> bool:
        """查询复读提示是否开启，默认开启"""
        val = await self.redis.get(f"qq_group:{group_id}:echo_enabled")
        return val is None or val == "1"

    async def set_enabled(self, group_id: int, enabled: bool) -> None:
        """设置复读提示开关状态"""
        await self.redis.set(
            f"qq_group:{group_id}:echo_enabled",
            "1" if enabled else "0",
        )


content_echo_redis = ContentEchoRedis()
