from abc import ABC, abstractmethod

# Controller base para outros controllers
class BaseController(ABC):
    def __init__(self, bot):
        self.bot = bot
        self.register()

    @abstractmethod
    def register(self):
        ...
