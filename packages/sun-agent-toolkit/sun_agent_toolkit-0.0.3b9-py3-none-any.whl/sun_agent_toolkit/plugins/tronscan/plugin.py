from dataclasses import dataclass

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .service import TronScanService


@dataclass
class TronScanPluginOptions:
    api_key: str | None = None


class TronScanPlugin(PluginBase[WalletClientBase]):
    def __init__(self, options: TronScanPluginOptions | None = None):
        if options is None:
            options = TronScanPluginOptions()
        super().__init__("tronscan", [TronScanService(options.api_key)])

    def supports_chain(self, chain: Chain) -> bool:
        chain_type = chain.get("type")
        if chain_type == "tron":
            return True
        chain_id = chain.get("id")
        return isinstance(chain_id, str) and chain_id.startswith("tron")


def tronscan(options: TronScanPluginOptions | None = None) -> TronScanPlugin:
    return TronScanPlugin(options)
