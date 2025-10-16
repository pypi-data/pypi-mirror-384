import asyncio
import logging
import os
from typing import Any

import aiohttp

from sun_agent_toolkit.core.decorators.tool import Tool

from .parameters import (
    GetAccountInfoParameters,
    GetAccountTransactionsParameters,
    GetTokenHoldersParameters,
    GetTokenInfoParameters,
    GetTransactionParameters,
    GetTronStatsParameters,
    GetWitnessesParameters,
    SearchTronParameters,
)

logger = logging.getLogger(__name__)


class TronScanService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        # Determine base_url by network env
        network = os.getenv("TRON_NETWORK", "shasta").lower()
        if network in ("mainnet", "main", "tron", "prod"):
            self.base_url = "https://apilist.tronscanapi.com/api"
        elif network in ("nile",):
            self.base_url = "https://nileapi.tronscan.org/api"
        else:  # default to shasta
            self.base_url = "https://shastapi.tronscan.org/api"
        # minimal runtime log of network and endpoint (filename & line via global formatter)
        logger.info("TronScanService initialized: network=%s base_url=%s", network, self.base_url)
        self.headers = {"User-Agent": "Sun-Agent-Toolkit/1.0", "Accept": "application/json"}
        if api_key:
            self.headers["TRON-PRO-API-KEY"] = api_key

    async def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make HTTP request to TronScan API"""
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"TronScan API error! Status: {response.status}, Response: {error_text}")
            except aiohttp.ClientError as e:
                raise Exception(f"Network error when calling TronScan API: {str(e)}") from e

    @Tool(
        {
            "description": "Get the list of witnesses",
            "parameters_schema": GetWitnessesParameters,
        }
    )
    async def get_witnesses(self, parameters: dict[str, Any]) -> dict[str, Any]:
        witness_type = int(parameters["witness_type"])
        top_n = int(parameters["top_n"])
        try:
            response: dict[str, Any] = await self._make_request("/pagewitness", {"witness_type": witness_type})
            num = min(response["total"], top_n)
            return {"num": num, "witnesses": response["data"][:num]}
        except Exception as e:
            return {"error": str(e)}

    @Tool(
        {
            "description": "Get detailed account information from TronScan including balance and tokens",
            "parameters_schema": GetAccountInfoParameters,
        }
    )
    async def get_account_info(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get detailed account information from TronScan"""
        address = parameters["address"]
        include_tokens = parameters.get("include_tokens", True)

        try:
            # Get basic account info
            account_data: dict[str, Any] = await self._make_request("/account", {"address": address})

            result: dict[str, Any] = {"address": address, "basic_info": account_data}

            # Get token balances if requested
            if include_tokens:
                try:
                    token_data: dict[str, Any] = await self._make_request(
                        "/account/tokens", {"address": address, "start": 0, "limit": 50}
                    )
                    result["tokens"] = token_data
                except Exception as e:
                    result["tokens_error"] = str(e)

            return result

        except Exception as e:
            return {"error": str(e), "address": address}

    @Tool(
        {
            "description": "Get detailed transaction information from TronScan",
            "parameters_schema": GetTransactionParameters,
        }
    )
    async def get_transaction(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get detailed transaction information from TronScan"""
        tx_hash = parameters["tx_hash"]

        try:
            data: dict[str, Any] = await self._make_request("/transaction-info", {"hash": tx_hash})
            return {"transaction_hash": tx_hash, "data": data}
        except Exception as e:
            return {"error": str(e), "transaction_hash": tx_hash}

    @Tool(
        {
            "description": "Get transaction history for a TRON address from TronScan",
            "parameters_schema": GetAccountTransactionsParameters,
        }
    )
    async def get_account_transactions(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get transaction history for a TRON address"""
        address = parameters["address"]
        limit = min(parameters.get("limit", 20), 200)  # Cap at 200
        start = parameters.get("start", 0)
        sort = parameters.get("sort", "-timestamp")
        only_confirmed = parameters.get("only_confirmed", True)

        try:
            params: dict[str, Any] = {"sort": sort, "count": "true", "limit": limit, "start": start, "address": address}

            if only_confirmed:
                params["confirmed"] = "true"

            data: dict[str, Any] = await self._make_request("/transaction", params)

            return {
                "address": address,
                "transactions": data.get("data", []),
                "total": data.get("total", 0),
                "pagination": {"start": start, "limit": limit, "has_more": len(data.get("data", [])) == limit},
            }

        except Exception as e:
            return {"error": str(e), "address": address}

    @Tool({"description": "Get TRC20 token information from TronScan", "parameters_schema": GetTokenInfoParameters})
    async def get_token_info(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get TRC20 token information from TronScan"""
        contract_address = parameters["contract_address"]

        try:
            data: dict[str, Any] = await self._make_request("/token_trc20", {"contract": contract_address})
            if "total" not in data or data["total"] == 0 or "trc20_tokens" not in data:
                return {"error": "TRC20 not found", "contract_address": contract_address}
            return {"contract_address": contract_address, "token_info": data["trc20_tokens"][0]}
        except Exception as e:
            return {"error": str(e), "contract_address": contract_address}

    @Tool(
        {"description": "Get token holders information from TronScan", "parameters_schema": GetTokenHoldersParameters}
    )
    async def get_token_holders(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get token holders information from TronScan"""
        contract_address = parameters["contract_address"]
        limit = min(parameters.get("limit", 20), 100)  # Cap at 100
        start = parameters.get("start", 0)

        try:
            params: dict[str, Any] = {"contract_address": contract_address, "start": start, "limit": limit}

            data: dict[str, Any] = await self._make_request("/token_trc20/holders", params) or {}
            holders = data.get("trc20_tokens", [])
            total = data.get("total", 0)

            return {
                "contract_address": contract_address,
                "holders": holders,
                "total_holders": total,
                "pagination": {"start": start, "limit": limit, "has_more": len(holders) < total},
            }

        except Exception as e:
            return {"error": str(e), "contract_address": contract_address}

    @Tool({"description": "Get TRON network statistics from TronScan", "parameters_schema": GetTronStatsParameters})
    async def get_tron_stats(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get TRON network statistics from TronScan"""
        try:
            # Get multiple stats endpoints
            stats_tasks: list[Any] = [
                self._make_request("/system/status"),
                self._make_request("/stats/overview"),
            ]

            try:
                results: list[Any] = await asyncio.gather(*stats_tasks, return_exceptions=True)

                response: dict[str, Any] = {"network_stats": {}}

                if not isinstance(results[0], Exception):
                    response["network_stats"]["system_status"] = results[0]

                if not isinstance(results[1], Exception):
                    response["network_stats"]["overview"] = results[1]

                return response

            except Exception as e:
                return {"error": f"Failed to gather network stats: {str(e)}"}

        except Exception as e:
            return {"error": str(e)}

    @Tool(
        {
            "description": "Search TRON blockchain data (addresses, transactions, tokens) on TronScan",
            "parameters_schema": SearchTronParameters,
        }
    )
    async def search_tron(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Search TRON blockchain data on TronScan"""
        query = parameters["query"]
        search_type = parameters.get("type", "all")

        try:
            # Determine what type of data we're searching for
            if len(query) == 64:  # Transaction hash
                if search_type in ["transaction", "all"]:
                    return await self.get_transaction({"tx_hash": query})
            elif len(query) == 34 and query.startswith("T"):  # TRON address
                if search_type in ["address", "all"]:
                    return await self.get_account_info({"address": query, "include_tokens": True})
            else:
                # General search
                params: dict[str, Any] = {"q": query}
                data: dict[str, Any] = await self._make_request("/search", params)

                return {"query": query, "search_type": search_type, "results": data}

            # If we reach here, either search_type filtered out results or pattern didn't match; fallback to general search
            params = {"q": query}
            data = await self._make_request("/search", params)
            return {"query": query, "search_type": search_type, "results": data}

        except Exception as e:
            return {"error": str(e), "query": query}
