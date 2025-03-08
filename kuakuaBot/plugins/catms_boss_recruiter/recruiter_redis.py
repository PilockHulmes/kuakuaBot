from redis.asyncio import Redis
import time
import json

redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)

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
    
    async with redis.pipeline(transaction=True) as pipe:
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
    info_str = await redis.hget(
        name=BM_RECRUIT.format(group_id=group_id),
        key=qq
    )
    if info_str == "":
        return False
    info = json.loads(info_str)
    async with redis.pipeline(transaction=True) as pipe:
        await pipe.hdel(BM_RECRUIT.format(group_id=group_id), qq)
        for member in info["members"]:
            await pipe.hdel(BM_RECRUIT_JOINED.format(group_id=group_id), member)
        # timeline 就不删了，反正下次再更新就可以

async def getJoined(group_id, qq):
    joined = await redis.hget(BM_RECRUIT_JOINED.format(group_id=group_id))
    if joined == "":
        return None
    info_str = await redis.hget(
        name=BM_RECRUIT.format(group_id=group_id),
        key=joined
    )
    if info_str == "":
        return None
    return json.loads(info_str)

async def bump(group_id, qq):
    await redis.zadd(
        name=BM_RECRUIT_TIMELINE.format(group_id=group_id),
        mapping={qq: time.time() * 1000},
        xx=True
    )