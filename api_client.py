import os
from typing import Tuple
import aiohttp
import logging
from datetime import datetime
import urllib.parse
from decimal import Decimal
import pytz

from dateutil import parser

from aiohttp.helpers import BasicAuth
from attr import dataclass
from discord.member import Member

from exceptions import ApiException, ConfigurationException

log = logging.getLogger()


class ApiClient:
    def __init__(self) -> None:
        self._api_host = os.environ.get("API_HOST")
        if self._api_host is None:
            raise ConfigurationException(f"API_HOST not set")

        self._api_port = os.environ.get("API_PORT")
        if self._api_port is None:
            raise ConfigurationException(f"API_PORT not set")

        self._basic_auth_user = os.environ.get("API_USERNAME")
        if self._basic_auth_user is None:
            raise ConfigurationException(f"API_USERNAME not set")

        self._basic_auth_pass = os.environ.get("API_PASSWORD")
        if self._basic_auth_pass is None:
            raise ConfigurationException(f"API_PASSWORD not set")

    def _build_url(self, endpoint: str) -> str:
        return f"http://{self._api_host}:{self._api_port}/{endpoint}"

    def _get_auth(self):
        return BasicAuth(login=self._basic_auth_user, password=self._basic_auth_pass)

    def _build_full_discord_name(self, member: Member) -> str:
        return str(member)

    async def get_wallet(self, discord_member: Member):
        discord_id = urllib.parse.quote(self._build_full_discord_name(discord_member))
        log.info(f"Getting wallet for {discord_member}")
        url = self._build_url(f"wallets/{discord_id}")

        async with aiohttp.ClientSession(auth=self._get_auth()) as session:
            async with session.get(url) as response:
                wallet = await response.json()
                if wallet.get("detail") == "Not found.":
                    return None
                return wallet

    async def make_wallet(self, discord_member: Member):
        """
        Make a wallet for the
        """
        log.info(f"Making new wallet for {discord_member}")
        url = self._build_url(f"wallets/")

        async with aiohttp.ClientSession(auth=self._get_auth()) as session:
            async with session.post(
                url, data={"discord_id": self._build_full_discord_name(discord_member)}
            ) as response:
                wallet = await response.json()
                return wallet

    async def delete_wallet(self, discord_member: Member):
        """
        Deletes the given user's wallet.
        """
        log.info(f"Deleting wallet for {discord_member}")
        discord_id = urllib.parse.quote(self._build_full_discord_name(discord_member))
        url = self._build_url(f"wallets/{discord_id}")

        async with aiohttp.ClientSession(auth=self._get_auth()) as session:
            async with session.delete(url) as response:
                status = response.status
                if status != 204:
                    log.error(f"Failed to delete wallet for {discord_member}")
                    raise ApiException(f"Failed to delete wallet for {discord_member}")

    async def send_bcoin(
        self, discord_member: Member, other_member: Member, amount: Decimal
    ):
        """
        Sends bcoin from discord_member to other_member if possible, raises an ApiException if not.
        """
        log.info(f"Sending B{amount} from {discord_member} to {other_member}")
        url = self._build_url("transactions/")

        payload = {
            "source": self._build_full_discord_name(discord_member),
            "destination": self._build_full_discord_name(other_member),
            "amount": amount,
        }
        async with aiohttp.ClientSession(auth=self._get_auth()) as session:
            async with session.post(url, data=payload) as response:
                if response.status == 404:
                    log.error(
                        f"Bruh you can't send bcoin unless both of you got wallets"
                    )
                    raise ApiException(
                        f"Bruh you can't send bcoin unless both of you got wallets"
                    )
                elif response.status == 409:
                    log.error(f"You don't got the funds homie")
                    raise ApiException(f"You don't got the funds homie")
                elif response.status != 201:
                    response_body = await response.json()
                    detail = response_body.get("detail")

                    if detail:
                        message = detail
                    else:
                        message = f"You not sendin shit today, something back here is busted: {response.status} {response_body}"

                    log.error(message)
                    raise ApiException(message)

    @staticmethod
    def pretty_print_transaction_history(wallet) -> str:
        """
        Writes the given wallet's transaction history to a pretty string
        """
        output = f"{wallet['discord_id']}'s Transaction History\n\n"
        transactions = [
            Transaction.from_response(transaction)
            for transaction in wallet["transaction_history"]
        ]
        for transaction in transactions:
            amount = transaction.destination_transfer.amount
            day, time = transaction.destination_transfer.date_components

            if transaction.source_transfer is None:
                transaction_message = (
                    f"{day} {time} - You summoned B{amount} from the void"
                )
            elif transaction.source_transfer.wallet.discord_id != wallet["discord_id"]:
                transaction_message = f"{day} {time} - {transaction.source_transfer.wallet.discord_id} sent you B{amount}"
            else:
                transaction_message = f"{day} {time} - You sent {transaction.destination_transfer.wallet.discord_id} B{amount}"

            output += transaction_message + "\n"
        return f"```{output}```"


# Helper classes
@dataclass
class Wallet:
    id: int
    discord_id: str

    @classmethod
    def from_response(cls, response: dict):
        return cls(
            id=int(response["id"]),
            discord_id=response["discord_id"],
        )


@dataclass
class CoinTransfer:
    wallet: Wallet
    transaction_id: int
    amount: Decimal
    date: datetime

    @classmethod
    def from_response(cls, response: dict):
        if response:
            date = parser.parse(response["date"])
            return cls(
                wallet=Wallet.from_response(response["wallet"]),
                transaction_id=int(response["transaction_id"]),
                amount=Decimal(response["amount"]),
                date=date,
            )
        else:
            return None

    @property
    def date_components(self) -> Tuple[str, str]:
        est = pytz.timezone("US/Eastern")  # Cuz mountain time isn't real

        day_component = self.date.astimezone(est).strftime("%m/%d/%Y")
        time_component = self.date.astimezone(est).strftime("%H:%M:%S")
        return day_component, time_component


@dataclass
class Transaction:
    transaction_id: int
    source_transfer: CoinTransfer
    destination_transfer: CoinTransfer

    @classmethod
    def from_response(cls, response: dict):
        return cls(
            transaction_id=int(response["transaction_id"]),
            source_transfer=CoinTransfer.from_response(response["source_transfer"]),
            destination_transfer=CoinTransfer.from_response(
                response["destination_transfer"]
            ),
        )
