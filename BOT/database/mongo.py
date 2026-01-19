from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB
import sys

class MongoDB:
    _client = None
    _db = None

    @classmethod
    async def connect(cls):
        if cls._client:
            return

        if not MONGO_URI:
            print("❌ MONGO_URI não definida")
            sys.exit(1)

        try:
            cls._client = AsyncIOMotorClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000
            )

            # 🔥 TESTE REAL DE CONEXÃO
            await cls._client.admin.command("ping")

            cls._db = cls._client[MONGO_DB]

            print("✅ MongoDB conectado com sucesso")

        except Exception as e:
            print("❌ Falha ao conectar no MongoDB")
            print(f"Erro: {e}")
            sys.exit(1)

    @classmethod
    def db(cls):
        if cls._db is None:
            raise RuntimeError("MongoDB não conectado")
        return cls._db

