import os
import logging
from dotenv import load_dotenv

# Função para obter variáveis de ambiente
def get_envs(required: list[str], optional: list[str] = None) -> dict:
    load_dotenv()
    envs = {}

    for key in required:
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"{key} não definido ou vazio")
        envs[key] = value

    if optional:
        for key in optional:
            envs[key] = os.getenv(key)

    return envs

env = get_envs(
    required=["TOKEN_BOT_DISCORD", 'MONGO_URI', 'MONGO_DB']

)

TOKEN_BOT = env["TOKEN_BOT_DISCORD"]
MONGO_URI = env['MONGO_URI']
MONGO_DB = env['MONGO_DB']
