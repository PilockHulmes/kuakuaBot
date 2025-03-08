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

class RecuriterRedis():
    async def create(self, group_id, qq, slots, nickname):
        info = {
            "recruit_id": qq,
            "group_id": group_id,
            "members": [qq],
            "members_nickname": [nickname],
            "timeline": time.time(),
            "slots": slots,
            "head_nickname": nickname,
        }
        
        async with redis_client.pipeline(transaction=True) as pipe:
            info_str = await pipe.hget(
                name=BM_RECRUIT.format(group_id=group_id),
                key=qq,
            )
            if info_str != "":
                return (False, "已经发布过互带车了，不能重复发布")
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
                mapping={qq: info["timeline"]}
            )
            await pipe.execute()
            return (True, "成功发布互带车！")

    async def dismiss(self, group_id, qq):
        async with redis_client.pipeline(transaction=True) as pipe:
            try:
                source_key = BM_RECRUIT.format(group_id=group_id)
                pipe.watch(source_key)
                info_str = await pipe.hget(
                    name=BM_RECRUIT.format(group_id=group_id),
                    key=qq
                )
                if info_str == "":
                    return (False, "没有发布过互带车，散车失败")
                info = json.loads(info_str)
                await pipe.hdel(BM_RECRUIT.format(group_id=group_id), qq)
                for member in info["members"]:
                    await pipe.hdel(BM_RECRUIT_JOINED.format(group_id=group_id), member)
                await pipe.execute()
                # timeline 就不删了，反正下次再更新就可以
                return (False, "散车成功")
            except redis.WatchError:
                return (False, "并发问题，散车失败，请重试")

    async def getJoined(self, group_id, qq):
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

    async def join(self, group_id, qq, target, nickname):
        async with redis_client.pipeline(transaction=True) as pipe:
            try:
                source_key = BM_RECRUIT.format(group_id=group_id)
                pipe.watch(source_key)
                if not await pipe.hexists(source_key, target):
                    return (-1, "车不存在，参加失败")
                info = json.loads(
                    await pipe.hget(source_key, target)
                )
                if info["slots"] <= 0:
                    return (-1, "车满，参加失败")
                info["members"].append(qq)
                info["members_nickname"].append(nickname)
                info["slots"] -= 1
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
                return (info["slots"], "上车成功")
            except redis.WatchError:
                return (-1, "并发问题，上车失败，请重试")

    async def leave(self, group_id, qq, nickname):
        async with redis_client.pipeline(transaction=True) as pipe:
            try:
                source_key = BM_RECRUIT.format(group_id=group_id)
                pipe.watch(source_key)
                
                target = await pipe.hget(
                    name=BM_RECRUIT_JOINED.format(group_id=group_id), 
                    key=qq
                )
                if target == "":
                    return (False, "没上任何互带车，下车失败")
                if target == str(qq):
                    return (False, "车头不能下车，有需要请解散车")
                info_str = await pipe.hget(
                    name=source_key,
                    key=target
                )
                if info_str == "": # 如果不知道怎么的车没了，那就下车
                    await pipe.hdel(BM_RECRUIT_JOINED.format(group_id=group_id), qq)
                else:
                    info = json.loads(info_str)
                    info["members"].remove(qq)
                    if nickname in info["members_nickname"]:
                        info["members_nickname"].remove(nickname)
                    info["slots"] += 1
                    await pipe.hset(
                        name=source_key,
                        key=target,
                        value=json.dumps(info),
                    )
                await pipe.execute()
                return (True, "下车成功")
            except redis.WatchError:
                return (False, "并发问题，下车失败，请重试")

    async def list(self, group_id):
        members_str = await redis_client.hgetall(BM_RECRUIT.format(group_id=group_id))
        return [json.loads(member_str) for member_str in members_str.values()]

    async def bump(self, group_id, qq):
        await redis_client.zadd(
            name=BM_RECRUIT_TIMELINE.format(group_id=group_id),
            mapping={qq: time.time() * 1000},
            xx=True
        )

operator = RecuriterRedis()