import os
import redis.asyncio as redis
import json
from connection import manager

redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

async def redis_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("tandemtask_events")

    async for message in pubsub.listen():
        if message["type"] == "message":
            continue
        data = json.loads(message["data"])
        await manager.deliver_local(data["workspace_id"], data["payload"])