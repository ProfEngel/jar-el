import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Pfad zu deinem MCP-Server-Script
    server_script = "/jar-el/mcp/jar_el_memory_server.py"

    server_params = StdioServerParameters(
        command="python3",
        args=[server_script],
        env=os.environ,  # vererbt deine .env-Variablen, falls nötig
    )

    # stdio_client startet den Server als Subprozess
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # MCP-Handshake
            init = await session.initialize()
            print("Verbunden mit MCP-Server:")
            print(f"  Name:    {init.serverInfo.name}")
            print(f"  Version: {init.serverInfo.version}")
            print()

            # Tools anzeigen
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            print("Verfügbare Tools:", tool_names)
            print()

            # Test 1: memory_search
            print("=== Test: memory_search ===")
            result = await session.call_tool(
                "memory_search",
                {
                    "query": "KI-Literacy",
                    "top_k": 5,
                },
            )
            # result.content ist eine Liste von Text/Binary-Content-Objekten
            if result.content:
                first = result.content[0]
                print("Antwort von memory_search:\n")
                print(first.text)  # TextContent
            else:
                print("Keine Content-Elemente zurückgegeben.")

            print()
            # Test 2: memory_observe
            print("=== Test: memory_observe ===")
            observe_result = await session.call_tool(
                "memory_observe",
                {
                    "text": "Ich plane, Jar-El im Kurs KI-Literacy als zentrales Memory-System zu verwenden.",
                    "role": "user",
                    "channel": "chat",
                },
            )
            if observe_result.content:
                first = observe_result.content[0]
                print("Antwort von memory_observe:\n")
                print(first.text)
            else:
                print("Keine Content-Elemente zurückgegeben.")


if __name__ == "__main__":
    asyncio.run(main())
