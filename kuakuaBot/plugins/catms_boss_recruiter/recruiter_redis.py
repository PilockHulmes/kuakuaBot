from redis.asyncio import Redis
import redis
import time
import json
from nonebot import logger

redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)

TYPE_BM = "bm"

BM_RECRUIT = "qq_group:{group_id}:bm_recruit"
BM_RECRUIT_TIMELINE = "qq_group:{group_id}:bm_recruit:timeline"
BM_RECRUIT_JOINED = "qq_group:{group_id}:bm_recruit:joined"

async def create(group_id, qq, slots):
    info = {
        "recruit_id": qq,
        "group_id": group_id,
        "members": [qq]
    }
    
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.hset(
            name=BM_RECRUIT.format(group_id=group_id),
            key=qq,
            value=json.dumps(info),
        )
        await pipe.hset(
            name=BM_RECRUIT_JOINED.format(group_id=group_id),
            key=qq,
            value=qq, # 参加了哪辆车
        )
        await pipe.zdd(
            name=BM_RECRUIT_TIMELINE.format(group_id=group_id),
            mapping={qq: time.time() * 1000}
        )
        await pipe.execute()

async def dismiss(group_id, qq):
    async with redis_client.pipeline(transaction=True) as pipe:
        try:
            source_key = BM_RECRUIT.format(group_id=group_id)
            pipe.watch(source_key)
            info_str = await pipe.hget(
                name=BM_RECRUIT.format(group_id=group_id),
                key=qq
            )
            if info_str == "":
                return "没有发车，散车失败"
            info = json.loads(info_str)
            await pipe.hdel(BM_RECRUIT.format(group_id=group_id), qq)
            for member in info["members"]:
                await pipe.hdel(BM_RECRUIT_JOINED.format(group_id=group_id), member)
            await pipe.execute()
            # timeline 就不删了，反正下次再更新就可以
            return "散车成功"
        except redis.WatchError:
            return "并发问题，散车失败，请重试"


async def getJoined(group_id, qq):
    async with redis_client.pipeline(transaction=True) as pipe:
        target = await pipe.hget(
            name=BM_RECRUIT_JOINED.format(group_id=group_id), 
            key=qq
        )
        if target == "":
            return None
        info_str = await pipe.hget(
            name=BM_RECRUIT.format(group_id=group_id),
            key=target
        )
        if info_str == "":
            return None
        await pipe.execute()
        return json.loads(info_str)

async def join(group_id, qq, target):
    async with redis_client.pipeline(transaction=True) as pipe:
        try:
            source_key = BM_RECRUIT.format(group_id=group_id)
            pipe.watch(source_key)
            if not await pipe.hexists(source_key, target):
                return "车不存在，参加失败"
            info = json.loads(
                await pipe.hget(source_key, target)
            )
            if len(info["members"]) >= 6:
                return "车满，参加失败"
            info["members"].append(qq)
            await pipe.hset(
                name=source_key,
                key=target,
                value=json.dumps(info),
            )
            await pipe.hset(
                name=BM_RECRUIT_JOINED.format(group_id=group_id),
                key=qq,
                value=target, # 参加了哪辆车
            )
            await pipe.execute()
            return "上车成功"
        except redis.WatchError:
            return "并发问题，上车失败，请重试"

async def leave(group_id, qq):
    async with redis_client.pipeline(transaction=True) as pipe:
        try:
            source_key = BM_RECRUIT.format(group_id=group_id)
            pipe.watch(source_key)
            
            target = await pipe.hget(
                name=BM_RECRUIT_JOINED.format(group_id=group_id), 
                key=qq
            )
            if target == "":
                return "没上任何车，下车失败"
            info_str = await pipe.hget(
                name=source_key,
                key=target
            )
            if info_str == "": # 如果不知道怎么的车没了，那就下车
                await pipe.hdel(BM_RECRUIT_JOINED.format(group_id=group_id), qq)
            else:
                info = json.loads(info_str)
                info["members"].remove(qq)
                await pipe.hset(
                    name=source_key,
                    key=target,
                    value=json.dumps(info),
                )
            await pipe.execute()
            return "下车成功"
        except redis.WatchError:
            return "并发问题，下车失败，请重试"

async def bump(group_id, qq):
    await redis_client.zadd(
        name=BM_RECRUIT_TIMELINE.format(group_id=group_id),
        mapping={qq: time.time() * 1000},
        xx=True
    )