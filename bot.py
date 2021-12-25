import os

from discord.ext import commands
from discord.ext.commands.bot import Bot
from dotenv import load_dotenv
import logging
import sys

from cogs import PERMITTED_CHANNELS, Economy, Wallet


# Setup some basic console logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    stream=sys.stdout,
    filemode="w",
    format=log_format,
    level=logging.INFO,
)
log = logging.getLogger()


def start_bot():
    log.info("Starting the bot")

    load_dotenv()

    TOKEN = os.getenv("DISCORD_TOKEN")

    bot: Bot = commands.Bot(command_prefix="!")
    bot.add_cog(Economy(bot))
    bot.add_cog(Wallet(bot))

    @bot.listen()
    async def on_ready():
        log.info("Bot is ready for some action")
        for guild in bot.guilds:
            log.info(
                f"Connected to guild {guild} - {guild.id} owned by {guild.owner_id}"
            )

            for member in guild.members:
                log.info(f"Guild member {member} - {member.id}")

            for channel in guild.channels:
                log.info(f"Guild channel {channel} - {channel.id}")

    bot.run(TOKEN)


if __name__ == "__main__":
    start_bot()
