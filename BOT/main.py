
from config import TOKEN_BOT
from services import Bot
from controllers.events import EventsController
from controllers.commands import CommandsController, CommandsAdmin
from controllers.mention import MentionController

from middleware.middlewares import LoggerMiddleware, BlockDMMiddleware, AdminRoleMiddleware

def main():
    bot = Bot()

    # middlewares (ordem importa)
    bot.use(LoggerMiddleware())
    bot.use(BlockDMMiddleware())
    bot.use(AdminRoleMiddleware(), admin=True)

    # controllers
    EventsController(bot)
    MentionController(bot)

    CommandsController(bot)
    CommandsAdmin(bot)

    bot.run(TOKEN_BOT)

if __name__ == "__main__":
    main()
