import logging
from typing import Any

from autogen_core.tools import FunctionTool

from sun_agent_toolkit.core import WalletClientBase

from .utils import get_on_chain_plugin_tools, get_on_chain_wallet_tools


def get_on_chain_tools(wallet: WalletClientBase, plugins: list[Any]) -> list[FunctionTool]:
    """Create autogen tools from SAT tools.

    Args:
        wallet: A wallet client instance
        plugins: List of plugin instances

    Returns:
        List of autogen Tool instances configured with the SAT tools
    """
    tools = get_on_chain_wallet_tools(wallet) + get_on_chain_plugin_tools(wallet, plugins)
    autogen_tools: list[FunctionTool] = []
    for t in tools:
        if hasattr(t, "func_or_tool"):
            try:
                tool = FunctionTool(t.func_or_tool, description=t.description)
                autogen_tools.append(tool)
            except Exception as e:
                logging.warning(f"跳过工具 {getattr(tool, 'name', 'unknown')}: {str(e)}")
                continue

    return autogen_tools
