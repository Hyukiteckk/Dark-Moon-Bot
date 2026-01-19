from database.mongo import MongoDB
from models.welcome import WelcomeModel

# Repositório para gerenciar configurações de boas-vindas
class WelcomeRepository:

    @staticmethod
    def collection():
        return MongoDB.db()["welcome"]

    @staticmethod
    async def save(model: WelcomeModel):
        await WelcomeRepository.collection().update_one(
            {"guild_id": model.guild_id},
            {"$set": model.to_dict()},
            upsert=True
        )

    @staticmethod
    async def get(guild_id: int) -> dict | None:
        return await WelcomeRepository.collection().find_one(
            {"guild_id": guild_id}
        )

