"""
UOP MCP Client for Python
"""

import httpx
from typing import Any, Dict, List, Optional

MCP_ENDPOINT = "https://api.unifiedoffer.com/functions/v1/mcp-http-wrapper"


class UOPMCPClient:
    """
    Client for Unified Offer Protocol MCP Server.

    Args:
        api_key: Your UOP API key. Get one at https://unifiedoffer.com
        endpoint: Optional custom endpoint URL
    """

    def __init__(self, api_key: str, endpoint: str = MCP_ENDPOINT):
        if not api_key:
            raise ValueError("API key is required. Get yours at https://unifiedoffer.com")
        self.api_key = api_key
        self.endpoint = endpoint
        self.client = httpx.Client()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def call_tool(self, tool_name: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool."""
        response = self.client.post(
            self.endpoint,
            json={
                "tool": tool_name,
                "arguments": args or {},
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            },
        )
        response.raise_for_status()
        return response.json()

    async def call_tool_async(self, tool_name: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool asynchronously."""
        response = await self.client.post(
            self.endpoint,
            json={
                "tool": tool_name,
                "arguments": args or {},
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            },
        )
        response.raise_for_status()
        return response.json()

    def search_products(self, query: str, **options) -> Dict[str, Any]:
        """Search for products."""
        return self.call_tool("searchProducts", {"query": query, **options})

    def generate_links(self, product_ids: List[str], **options) -> Dict[str, Any]:
        """Generate affiliate links."""
        return self.call_tool("generateLinks", {"productIds": product_ids, **options})

    def negotiate_price(self, product_id: str, requested_discount: float, **options) -> Dict[str, Any]:
        """Negotiate product price."""
        return self.call_tool("negotiatePrice", {
            "productId": product_id,
            "requestedDiscount": requested_discount,
            **options
        })

    def chat(self, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Send chat message."""
        args = {"message": message}
        if thread_id:
            args["threadId"] = thread_id
        return self.call_tool("chat", args)

    def list_threads(self) -> Dict[str, Any]:
        """List conversation threads."""
        return self.call_tool("listThreads", {})

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get thread details."""
        return self.call_tool("getThread", {"threadId": thread_id})

    def extend_thread(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Continue conversation in existing thread."""
        return self.call_tool("extendThread", {"threadId": thread_id, "message": message})
