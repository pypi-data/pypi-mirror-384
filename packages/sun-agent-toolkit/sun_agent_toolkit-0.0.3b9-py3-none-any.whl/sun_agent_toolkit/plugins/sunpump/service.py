import json
import logging
from datetime import datetime
from typing import Any, Literal

import aiohttp
from tronpy.keys import PrivateKey

from sun_agent_toolkit.core.decorators.tool import Tool
from sun_agent_toolkit.core.types.token import Token
from sun_agent_toolkit.wallets.tron.tron_wallet_client import TronWalletClient

from .abi import LAUNCH_PAD_ABI
from .parameters import (
    GetFeesParameters,
    GetTokenLaunchStatusParameters,
    SearchTokenParameters,
    TokenLaunchParameters,
)

logger = logging.getLogger(__name__)


class SunPumpService:
    def __init__(
        self,
        base_url: str = "https://tn-api.sunpump.meme/pump-api",
        openapi_base_url: str = "https://tn-api.sunpump.meme/pump-api",
        pump_contract: str = "",
        private_key: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.openapi_base_url = openapi_base_url.rstrip("/")  # Remove trailing slash if present
        self.pump_contract = pump_contract
        if private_key is not None:
            pk_hex = private_key[2:] if private_key.startswith("0x") else private_key
            try:
                self.private_key = PrivateKey(bytes.fromhex(pk_hex))
            except Exception as e:
                raise ValueError(f"Invalid private key format: {e}") from e

    async def _make_request(
        self, method: Literal["GET", "POST"], base_url: str, endpoint: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a request to the SunPump API."""
        url = f"{base_url}{endpoint}"

        headers: dict[str, Any] = {}

        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "GET":
                    request_coro = session.get(url, params=parameters, headers=headers)
                elif method.upper() == "POST":
                    request_coro = session.post(url, json=parameters, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                async with request_coro as response:
                    response_text = await response.text()
                    try:
                        response_json = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from {endpoint}: {response_text}") from e

                    logger.debug(f"\nAPI Response for {endpoint}:")
                    logger.debug(f"Status: {response.status}")
                    logger.debug(f"Headers: {dict(response.headers)}")
                    logger.debug(f"Body: {response_text}")

                    if not response.ok or response_json.get("code", -1) != 0:
                        error = response_json.get("msg", "Unknown error")
                        raise Exception(error)

                    return response_json
            except aiohttp.ClientError as e:
                raise Exception(f"Network error while accessing {endpoint}: {str(e)}") from e

    @Tool(
        {
            "name": "sunpump_search_token_by_symbol",
            "description": "search sunpump token by token symbol",
            "parameters_schema": SearchTokenParameters,
        }
    )
    async def search_token(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """search sunio token by token symbol"""
        try:
            response = await self._make_request(
                "GET",
                self.base_url,
                "/token/searchV2",
                {
                    "query": parameters["symbol"],
                    "sort": "marketCap:DESC",
                    "size": parameters["top_n"],
                    "page": "1",
                },
            )

            if not response or "data" not in response or not response["data"]["tokens"]:
                return {"success": True, "tokens": []}

            tokens: list[Token] = [
                {
                    "name": token["name"],
                    "symbol": token["symbol"],
                    "address": token["contractAddress"],
                    "decimals": token["decimals"],
                }
                for token in response["data"]["tokens"]
            ]
            return {"success": True, "tokens": tokens}
        except Exception as error:
            raise Exception(f"Failed to search token: {error}") from error

    @Tool(
        {
            "name": "sunpump_get_token_launch_status",
            "description": "get the launch status of a sunpump token",
            "parameters_schema": GetTokenLaunchStatusParameters,
        }
    )
    async def get_token_launch_status(
        self, wallet_client: TronWalletClient, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """get the status of sunpump token"""
        STATE_MAP = ["NEVER_CREATED", "ONSALE", "PENDING", "LAUNCHED"]
        try:
            token_state = int(
                wallet_client.read(
                    {
                        "address": self.pump_contract,
                        "abi": LAUNCH_PAD_ABI,
                        "functionName": "getTokenState",
                        "args": [parameters["token_address"]],
                    }
                )["value"]
            )
            return {"token_address": parameters["token_address"], "token_status": STATE_MAP[token_state]}
        except Exception as e:
            raise ValueError(f"Failed to fetch token state: {e}") from e

    async def _submit_launch_token_transaction(self, params: dict[str, str]) -> None:
        message = f"{params['createTxHash']} - {int(datetime.now().timestamp() * 1000)}"
        signature = self.private_key.sign_msg(message)
        params["thirdPlatUserAddress"] = self.private_key.public_key.to_base58check_address()
        params["message"] = message
        params["signature"] = str(signature)
        try:
            response = await self._make_request("POST", self.openapi_base_url, "/token/create", params)
            success = response.get("code") == 0 if response else False
            if not success:
                raise RuntimeError(response.get("msg", "UnknownError"))
        except Exception as error:
            raise Exception(f"Failed to submit launch token transaction: {error}") from error

    @Tool(
        {
            "name": "get_sunpump_fees",
            "description": "get the contract fees of sunpump",
            "parameters_schema": GetFeesParameters,
        }
    )
    async def get_sunpump_fees(self, wallet_client: TronWalletClient, parameters: dict[str, Any]) -> dict[str, Any]:
        """get the fees of sunpump contract
        Returns:
             mintFee: TRX cost in base units to launch a new pump token
             minTxFee: the min TRX cost in base units to purchase or sale pump token
        """
        try:
            mint_fee = int(
                wallet_client.read(
                    {
                        "address": self.pump_contract,
                        "abi": LAUNCH_PAD_ABI,
                        "functionName": "mintFee",
                        "args": [],
                    }
                )["value"]
            )
            min_tx_fee = int(
                wallet_client.read(
                    {
                        "address": self.pump_contract,
                        "abi": LAUNCH_PAD_ABI,
                        "functionName": "minTxFee",
                        "args": [],
                    }
                )["value"]
            )
            return {"mintFee": mint_fee, "minTxFee": min_tx_fee}
        except Exception as e:
            raise ValueError(f"Failed to fetch token state: {e}") from e

    @Tool(
        {
            "name": "sunpump_launch_token",
            "description": "launch a new sunpump token",
            "parameters_schema": TokenLaunchParameters,
        }
    )
    async def launch_token(self, wallet_client: TronWalletClient, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            unsigned_txn = wallet_client.build_transaction(
                {
                    "to": self.pump_contract,
                    "abi": LAUNCH_PAD_ABI,
                    "functionName": "createAndInitPurchase",
                    "args": [
                        parameters["name"],
                        parameters["symbol"],
                    ],
                    "value": int(wallet_client.convert_to_base_units({"amount": str(parameters["initialBuy"] + 20)})),
                    "feeLimit": 1000000000,
                }
            )
            signed_txn = await wallet_client.sign_transaction(unsigned_txn)
            params = parameters.copy()
            params["createTxHash"] = signed_txn["txID"]
            await self._submit_launch_token_transaction(params)
            return await wallet_client.broadcast_transaction(signed_txn)
        except Exception as e:
            raise ValueError(f"Failed to launch token: {e}") from e
