FROM python:3.12-slim

# System-Updates und Basis-Tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Server-Code und .env ins Image kopieren
COPY . .

# Standard-Umgebungsvariablen (können per env_file überschrieben werden)
ENV PORT=8765

# FastMCP-HTTP-Server exposed Port 8765
EXPOSE 8765

# Startet den Streamable-HTTP-MCP-Server
CMD ["python", "jar_el_memory_server_http.py"]

