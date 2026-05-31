import logging
import os
from typing import Optional
import httpx

logger = logging.getLogger(__name__)
MCP_SERVER_URL = "http://localhost:8001"


class MCPClient:
    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url

    async def call_tool(self, tool_name: str, arguments: dict = None):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/tools/call",
                    json={"tool": tool_name, "arguments": arguments or {}},
                )
                resp.raise_for_status()
                return resp.json().get("result", {})
        except Exception as e:
            logger.warning(f"MCP call failed ({tool_name}): {e} — using fallback")
            return self._fallback(tool_name)

    def _fallback(self, tool_name: str) -> dict:
        return {
            "recommandations": [
                "Repos recommande",
                "Hydratation suffisante",
                "Surveillance des symptomes",
                "Consultation medicale si aggravation",
            ],
            "source": "fallback_local",
        }

    async def get_general_care_recommendations(self, symptoms_description: str = "") -> dict:
        return await self.call_tool("general_care_tool", {"symptoms_description": symptoms_description})


_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        url = os.getenv("MCP_SERVER_URL", MCP_SERVER_URL)
        _mcp_client = MCPClient(base_url=url)
    return _mcp_client
