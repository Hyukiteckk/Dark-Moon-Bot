"""
Módulo de Comandos - Dark Moon Bot
Importa todos os comandos disponíveis
"""

from .pontos import setup_pontos_commands
from .moderacao import setup_moderacao_commands
from .imagens import setup_imagens_commands
from .clima import setup_clima_commands
from .ia import setup_ia_commands
from .carro import setup_carro_commands

__all__ = [
    "setup_pontos_commands",
    "setup_moderacao_commands",
    "setup_imagens_commands",
    "setup_clima_commands",
    "setup_ia_commands",
    "setup_carro_commands",
]
