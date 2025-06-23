from redis.asyncio import Redis

redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)

async def redis_listener():
    channel, = await redis.subscribe("smega_content")
    try:
        async for message in channel.iter():
            msg = message.decode("utf-8")
            yield msg
    finally:
        print("reading data from smega channel failed")