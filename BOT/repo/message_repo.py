from database.mongo import MongoDB

# Repositório para gerenciar contagem de mensagens dos usuários
class MessageRepository:

    @staticmethod
    def collection():
        return MongoDB.db()["messages"]

    @staticmethod
    async def add(guild_id: int, user_id: int):
        await MessageRepository.collection().update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {"$inc": {"count": 1}},
            upsert=True
        )

    @staticmethod
    async def top(guild_id: int, limit: int = 10):
        cursor = (
            MessageRepository.collection()
            .find({"guild_id": guild_id})
            .sort("count", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

