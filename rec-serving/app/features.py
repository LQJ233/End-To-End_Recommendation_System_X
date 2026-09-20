from typing import Dict, List, Optional

from redis.asyncio import Redis


class FeatureFetcher:
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client

    async def get_user_history(self, user_id: str) -> List[int]:
        values = await self.redis.lrange(f"adrec:user:history:{user_id}", 0, 20)
        return [int(value) for value in values]

    async def get_hot_items(self, limit: int = 20) -> List[int]:
        values = await self.redis.lrange("adrec:hot:items", 0, limit - 1)
        return [int(value) for value in values]

    async def get_cached_recall(self, user_id: str, limit: int = 50) -> List[int]:
        values = await self.redis.lrange(
            f"adrec:recall:cache:{user_id}",
            0,
            limit - 1,
        )
        return [int(value) for value in values]

    async def get_user_features(self, user_id: str) -> Dict[str, str]:
        return await self.redis.hgetall(f"adrec:user:features:{user_id}")

    async def get_item_features(self, item_id: int) -> Dict[str, str]:
        return await self.redis.hgetall(f"adrec:item:features:{item_id}")
