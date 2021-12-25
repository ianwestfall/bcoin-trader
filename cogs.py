from decimal import Decimal
import discord
from discord.ext import commands
import logging
import os

from discord.ext.commands.context import Context

from api_client import ApiClient
from exceptions import ApiException


log = logging.getLogger()


PERMITTED_CHANNELS = list(
    map(str.strip, os.environ.get("PERMITTED_CHANNELS", "").split(","))
)


def restrict_to_permitted_channels(ctx):
    """
    Make sure only commands from the configured channels are processed
    """
    return str(ctx.channel.id) in PERMITTED_CHANNELS


def get_currency_emoji(emoji_name, ctx: Context) -> str:
    """
    Given the desired emoji_name and context, return the message-ready emoji string if the emoji is present, otherwise 'B'.
    """
    emojis = list(filter(lambda emoji: emoji.name == emoji_name, ctx.guild.emojis))
    if len(emojis):
        return str(emojis[0])
    else:
        return "B"


class Economy(commands.Cog):
    """
    Commands for doing economic shit
    """

    def __init__(self, bot) -> None:
        self._bot = bot
        self._api_client = ApiClient()
        self._currency_emoji_name = os.environ.get("CURRENCY_EMOJI", "B").strip()

    @commands.command()
    @commands.check(restrict_to_permitted_channels)
    async def join(self, ctx):
        """
        Registers the user with a new wallet if they don't have one yet
        """
        member = ctx.author
        log.info(f"{member} wants to join the crypto economy")

        # See if they already have a wallet
        wallet = await self._api_client.get_wallet(member)
        currency_emoji = get_currency_emoji(self._currency_emoji_name, ctx)

        if wallet is not None:
            log.info(f"{member} is already signed up")

            await ctx.send(
                f"{member.mention}: Bruh you already signed up, you got {currency_emoji}{wallet['current_value']} rn"
            )
        else:
            log.info(f"Making a wallet for {member}")
            wallet = await self._api_client.make_wallet(member)
            await ctx.send(
                f"Aight welcome to the party, {member.mention}. Here's {currency_emoji}{wallet['current_value']} to get you started"
            )

    @commands.command()
    @commands.check(restrict_to_permitted_channels)
    async def transactions(self, ctx):
        """
        Check your transaction history
        """
        member = ctx.author
        log.info(f"{member} is checkin their receipts")

        # Grab their wallet
        wallet = await self._api_client.get_wallet(member)

        if wallet:
            message = self._api_client.pretty_print_transaction_history(wallet)
            await ctx.send(message)
        else:
            log.info(f"{member.mention}, you not even signed up yet ya big dummy")
            await ctx.send(f"{member.mention}, you not even signed up yet ya big dummy")

    @commands.command()
    @commands.check(restrict_to_permitted_channels)
    async def send(self, ctx, other_member: discord.Member = None, amount: Decimal = 0):
        """
        Send bcoin to your homies
        """
        member = ctx.author
        log.info(f"Sending B{amount} from {member} to {other_member}")
        currency_emoji = get_currency_emoji(self._currency_emoji_name, ctx)

        # Make the transaction and see what the API gods say
        try:
            await self._api_client.send_bcoin(member, other_member, amount)
            await ctx.send(
                f"Ayo {other_member.mention}, {member.mention} sent you {currency_emoji}{amount}"
            )
        except ApiException as e:
            await ctx.send(f"{member.mention} {str(e)}")


class Wallet(commands.Cog):
    """
    Commands for managing your wallet
    """

    def __init__(self, bot) -> None:
        self._bot = bot
        self._api_client = ApiClient()
        self._currency_emoji_name = os.environ.get("CURRENCY_EMOJI", "B").strip()

    @commands.command()
    @commands.check(restrict_to_permitted_channels)
    async def balance(self, ctx):
        """
        Checks the current balance in the user's wallet
        """
        member = ctx.author
        log.info(f"{member} wants to check their wallet balance")

        # Grab their wallet
        wallet = await self._api_client.get_wallet(member)
        currency_emoji = get_currency_emoji(self._currency_emoji_name, ctx)

        if wallet:
            log.info(f"{member} has {wallet['current_value']} in their wallet")
            await ctx.send(
                f"{member.mention}, you got {currency_emoji}{wallet['current_value']} in your wallet"
            )
        else:
            log.info(f"{member} doesn't have a wallet yet")
            await ctx.send(
                f"{member.mention}, you ain't even signed up yet homie chill"
            )
