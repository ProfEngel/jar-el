from jar_el_memory_server import mcp

if __name__ == "__main__":
    # Wunsch-Host/-Port für Streamable HTTP setzen
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8765

    # Streamable-HTTP-Server starten
    mcp.run(transport="streamable-http")

