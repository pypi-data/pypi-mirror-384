
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import copy
import threading

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from neuro_san.internals.run_context.langchain.mcp.mcp_clients_info_restorer import McpClientsInfoRestorer


class LangChainMcpAdapter:
    """
    Adapter class to fetch tools from a Multi-Client Protocol (MCP) server and return them as
    LangChain-compatible tools. This class provides static methods for interacting with MCP servers.
    """

    _mcp_info_lock: threading.Lock = threading.Lock()
    _mcp_clients_info: Dict[str, Any] = None

    def __init__(self):
        """
        Constructor
        """
        self.client_allowed_tools: List[str] = []

    @staticmethod
    def _load_mcp_clients_info():
        """
        Loads MCP clients information from a configuration file if not already loaded.
        """
        with LangChainMcpAdapter._mcp_info_lock:
            if LangChainMcpAdapter._mcp_clients_info is None:
                LangChainMcpAdapter._mcp_clients_info = McpClientsInfoRestorer().restore()
                if LangChainMcpAdapter._mcp_clients_info is None:
                    # Something went wrong reading the file.
                    # Prevent further attempts to load info.
                    LangChainMcpAdapter._mcp_clients_info = {}

    async def get_mcp_tools(
            self,
            server_url: str,
            allowed_tools: Optional[List[str]] = None,
    ) -> List[BaseTool]:
        """
        Fetches tools from the given MCP server and returns them as a list of LangChain-compatible tools.

        :param server_url: URL of the MCP server, e.g. https://mcp.deepwiki.com/mcp or http://localhost:8000/mcp/
        :param allowed_tools: Optional list of tool names to filter from the server's available tools.
                              If None, all tools from the server will be returned.

        :return: A list of LangChain BaseTool instances retrieved from the MCP server.
        """
        if self._mcp_clients_info is None:
            self._load_mcp_clients_info()

        mcp_tool_dict: Dict[str, Any] = {
            "url": server_url,
            "transport": "streamable_http",
        }
        # Try to look up authentication details from the URL
        headers_dict: Dict[str, Any] =\
            self._mcp_clients_info.get(server_url, {}).get("headers")
        if headers_dict:
            mcp_tool_dict["headers"] = copy.copy(headers_dict)

        client = MultiServerMCPClient(
            {"server": mcp_tool_dict}
        )

        # The get_tools() method returns a list of StructuredTool instances, which are subclasses of BaseTool.
        # Internally, it calls load_mcp_tools(), which uses an `async with create_session(...)` block.
        # This guarantees that any temporary MCP session created is properly closed when the block exits,
        # even if an error is raised during tool loading.
        # See: https://github.com/langchain-ai/langchain-mcp-adapters/blob/main/langchain_mcp_adapters/tools.py#L164
        # Optimization:
        #   It's possible we might want to cache these results somehow to minimize tool calls.
        mcp_tools: List[BaseTool] = await client.get_tools()

        # If allowed_tools is provided, filter the list to include only those tools.
        client_allowed_tools: List[str] = allowed_tools
        if client_allowed_tools is None:
            # Check if MCP client info has a "tools" field to use as allowed tools.
            client_allowed_tools = self._mcp_clients_info.get(server_url, {}).get("tools", [])
        # If client allowed tools is an empty list, do not filter the tools.
        if client_allowed_tools:
            mcp_tools = [tool for tool in mcp_tools if tool.name in client_allowed_tools]

        self.client_allowed_tools = client_allowed_tools

        for tool in mcp_tools:
            # Add "langchain_tool" tags so journal callback can idenitify it.
            # These MCP tools are treated as Langchain tools and can be reported in the thinking file.
            tool.tags = ["langchain_tool"]

        return mcp_tools
