import time
import discord
from repo.call_time_repo import CallTimeRepository


class CallTimeService:

    @staticmethod
    def is_active_state(vs: discord.VoiceState | None) -> bool:
        if not vs or not vs.channel:
            return False

        return not (
            vs.self_mute
            or vs.mute
            or vs.self_deaf
            or vs.deaf
            or vs.suppress
        )

    @staticmethod
    async def join_call(guild_id: int, user_id: int):
        now = time.time()
        data = await CallTimeRepository.get(guild_id, user_id)

        if data is None or not data.get("joined_at"):
            await CallTimeRepository.set_join(guild_id, user_id, now)

    @staticmethod
    async def leave_call(guild_id: int, user_id: int):
        data = await CallTimeRepository.get(guild_id, user_id)
        if not data or not data.get("joined_at"):
            return

        elapsed = int(time.time() - data["joined_at"])
        if elapsed > 0:
            await CallTimeRepository.add_time(guild_id, user_id, elapsed)

        await CallTimeRepository.clear_join(guild_id, user_id)

    @staticmethod
    def format_time(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"
