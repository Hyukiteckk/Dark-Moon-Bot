from database.mongo import MongoDB

# Repositório para gerenciar tempos de chamada dos usuários
class CallTimeRepository:

    @staticmethod
    def collection():
        return MongoDB.db()["call_time"]

    @staticmethod
    async def get(guild_id: int, user_id: int):
        return await CallTimeRepository.collection().find_one({
            "guild_id": guild_id,
            "user_id": user_id
        })

    @staticmethod
    async def set_join(guild_id: int, user_id: int, timestamp: float):
        await CallTimeRepository.collection().update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$set": {"joined_at": timestamp},
                "$setOnInsert": {"total_seconds": 0}
            },
            upsert=True
        )

    @staticmethod
    async def add_time(guild_id: int, user_id: int, seconds: int):
        await CallTimeRepository.collection().update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$inc": {"total_seconds": seconds},
                "$set": {"joined_at": None}
            }
        )

    @staticmethod
    async def top(guild_id: int, limit: int = 10):
        cursor = (
            CallTimeRepository.collection()
            .find({"guild_id": guild_id})
            .sort("total_seconds", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    @staticmethod
    async def update(guild_id, user_id, **fields):
        await collection.update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {"$set": fields},
            upsert=True
        )

