from dataclasses import dataclass

# Modelo para armazenar informações de tempo de chamada dos usuários
@dataclass
class CallTimeModel:
    guild_id: int
    user_id: int
    total_seconds: int = 0
    joined_at: float | None = None
    points: int = 0

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "total_seconds": self.total_seconds,
            "joined_at": self.joined_at,
            "points": self.points
        }

