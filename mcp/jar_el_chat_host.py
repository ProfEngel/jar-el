import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


# OpenAI-kompatibles Chat-LLM für die eigentliche Antwort
CHAT_API_KEY = os.getenv("CHAT_API_KEY", os.getenv("OPENAI_API_KEY"))
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", os.getenv("OPENAI_BASE_URL"))
CHAT_MODEL = os.getenv("CHAT_CHAT_MODEL", "gpt-oss-65k:latest")

if not CHAT_API_KEY or not CHAT_BASE_URL:
    raise RuntimeError("CHAT_API_KEY oder CHAT_BASE_URL fehlen")

chat_client = OpenAI(api_key=CHAT_API_KEY, base_url=CHAT_BASE_URL)


async def chat_loop():
    server_script = "/jar-el/mcp/jar_el_memory_server.py"

    server_params = StdioServerParameters(
        command="python3",
        args=[server_script],
        env=os.environ,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"Verbunden mit MCP-Server {init.serverInfo.name} v{init.serverInfo.version}")
            tools_result = await session.list_tools()
            print("Verfügbare Tools:", [t.name for t in tools_result.tools])
            print()

            history = []  # [(role, content), ...]

            while True:
                try:
                    user_input = input("Du: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nBeende Chat.")
                    break

                if not user_input:
                    continue

                # 1) Relevante Erinnerungen holen
                search_result = await session.call_tool(
                    "memory_search",
                    {
                        "query": user_input,
                        "top_k": 5,
                    },
                )
                memory_context = ""
                if search_result.content:
                    memory_context = search_result.content[0].text

                # 2) Aktuelle Nachricht im Hintergrund beobachten/speichern
                try:
                    _ = await session.call_tool(
                        "memory_observe",
                        {
                            "text": user_input,
                            "role": "user",
                            "channel": "chat",
                        },
                    )
                except Exception as exc:
                    print(f"[Warnung] memory_observe fehlgeschlagen: {exc}")

                # 3) Chat-LLM mit Memory-Kontext aufrufen
                system_prompt = (
                    "Du bist ein persönlicher Assistent. "
                    "Nutze den bereitgestellten Memory-Kontext, wenn er relevant ist, "
                    "aber erfinde keine Fakten dazu."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                ]

                if memory_context:
                    messages.append(
                        {
                            "role": "system",
                            "content": f"Relevante Erinnerungen aus Jar-El:\n\n{memory_context}",
                        }
                    )

                # bisherige Unterhaltung anhängen
                for role, content in history:
                    messages.append({"role": role, "content": content})

                # aktuelle User-Nachricht
                messages.append({"role": "user", "content": user_input})

                resp = chat_client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    temperature=0.3,
                )

                assistant_reply = resp.choices[0].message.content
                print(f"Jar-Host: {assistant_reply}\n")

                # Verlauf aktualisieren
                history.append(("user", user_input))
                history.append(("assistant", assistant_reply))


if __name__ == "__main__":
    asyncio.run(chat_loop())
