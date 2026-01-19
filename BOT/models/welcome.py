# models/welcome.py


# Modelo para armazenar configurações de boas-vindas do servidor
class WelcomeModel:
    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        message: str,
        image: str | None = None
    ):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message = message
        self.image = image

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message": self.message,
            "image": self.image
        }

