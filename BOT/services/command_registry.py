 
from collections import defaultdict
from discord.app_commands import Command

# registro de novos comandos
def get_commands_by_category(tree):
    categories = defaultdict(list)

    for cmd in tree.walk_commands():
        if not isinstance(cmd, Command):
            continue

        category = cmd.extras.get("category", "outros")
        categories[category].append(cmd)

    return categories

