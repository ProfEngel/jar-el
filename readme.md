# Jar-El 🧠

![GitHub stars](https://img.shields.io/github/stars/ProfEngel/Jar-El?style=social)
![GitHub forks](https://img.shields.io/github/forks/ProfEngel/Jar-El?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/ProfEngel/Jar-El?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/ProfEngel/Jar-El)
![GitHub language count](https://img.shields.io/github/languages/count/ProfEngel/Jar-El)
![GitHub top language](https://img.shields.io/github/languages/top/ProfEngel/Jar-El)
![GitHub last commit](https://img.shields.io/github/last-commit/ProfEngel/Jar-El?color=red)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![YouTube](https://img.shields.io/badge/YouTube-MatMaxEngel-red?logo=youtube&logoColor=white)](https://www.youtube.com/user/MatMaxEngel)

**Jar-El is a Personal Semantic Operating System (S-OS) designed to act as a Digital Twin.**

Unlike static RAG systems, Jar-El features an active **"Self-Baking" memory architecture** and uses the **Model Context Protocol (MCP)** to orchestrate between devices (iPhone, Desktop, Server) and LLMs. It preserves not just data, but your reasoning style, emotions, and context, enabling autonomous agentic workflows.

This project is conceptualized by **Prof. Dr. Mathias Engel** as part of the research on personal AI agents and educational assistants.

> **🚀 Open Source & Free**
> 
> Jar-El is a pure open-source project. You can use, modify, and deploy it freely for personal or educational purposes.
>
> **Concept:** Local Memory (Privacy) + Remote Intelligence (API).
> **Goal:** A system that learns *how* you work, not just *what* you know.

***

## Key Features 🚀

- 🧠 **Digital Twin Core**: Learns and adapts to your writing style, emotional tone, and decision-making patterns.
- ♾️ **Self-Baking Memory**: Asynchronous consolidation of raw chat logs into structured, interconnected knowledge graphs in a vector database.
- 🔌 **Dual-Transport MCP**: Seamless integration via **SSE** (Web/Remote) and **Stdio** (Local Desktop) for universal client compatibility.
- ⚡ **Context Efficiency**: Implements the **Anthropic Orchestrator Pattern** (Scripting) to prevent context window saturation by dynamically loading tools.
- 🛠️ **Agentic Workflows**:
  - **Docling Integration**: Multimodal ingestion of PDFs/Images into semantic text.
  - **Reinforcement Learning**: Feedback loops comparing drafted vs. sent emails to optimize workflows.
- 🌍 **Hybrid Architecture**: Runs on energy-efficient MiniPCs (8GB RAM) while offloading heavy compute to OpenAI-compatible APIs.
- 🔒 **Privacy First**: Your memory, secrets, and graph stay on your local server.

***

## How to Install 🚀

Full Installation Guide here [Installation and Use-Guide](howto.md).

### System Requirements

**Hardware:**
- **Host:** Simple MiniPC (x86/ARM) with approx. 8 GB RAM (e.g., Beelink, Minisforum, Mac Mini)
- **Storage:** 50 GB SSD space for Docker and Vector DB
- **Network:** Tailscale recommended for secure remote access

**Software:**
- **Docker & Docker Compose**
- **API Access:** OpenAI, OpenRouter, or a self-hosted HFWU-Server

### Quick Start

1. **Clone the Repository**

   ```bash
   git clone [https://github.com/ProfEngel/Jar-El.git](https://github.com/ProfEngel/Jar-El.git)
   cd Jar-El
   ````

2.  **Configuration**
    Create a `.env` file in the root directory:

    ```ini
    # Intelligence Provider
    OPENAI_API_KEY=sk-xxxx
    OPENAI_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)
    OPENAI_CHAT_MODEL=gpt-4o

    # Internal Config
    MEMORY_API_URL=http://memory-api:8000
    SELF_BAKER_INTERVAL=600
    MCP_SSE_PORT=8000
    ```

3.  **Launch the Stack**

    ```bash
    docker compose up -d --build
    ```

4.  **Connect Clients**

      - **OpenWebUI:** Add Tool -\> SSE -\> `http://YOUR-TAILSCALE-IP:8000/sse`
      - **LM Studio:** Edit `mcp.json` -\> Add Stdio command (via Docker exec)

-----

## What's Next? 🌟

**Short to medium-term roadmap:**

  - 🌍 **Context Orchestrator**: Advanced script-based routing to keep LLM context lean.
  - 📊 **GraphRAG Integration**: Upgrading the flat vector memory to a full Knowledge Graph (Neo4j/LiteGraph).
  - 🔗 **Desktop Automation**: MCP Server for local file system access and Office suite integration.
  - 📧 **Email & Calendar Agents**: Autonomous drafting and scheduling based on memory context.
  - 🧠 **RLHF Loop**: Automated "Draft vs. Sent" analysis to fine-tune the Digital Twin's personality.
  - 📱 **Mobile-Native App**: Dedicated iOS/Android client wrapping the MCP connection.

-----

## Project Overview (The Hard Facts) 📊

### Technical Specifications

**📁 Repository Scale:**

  - **Structured Modular Monorepo**
  - **Python:** Core logic (FastAPI, FastMCP, Workers)
  - **Docker:** Full containerization for portability
  - **Lines of Code:** \~3,500+ (Core Logic)

### Development Approach

**🎯 Design Philosophy:**

  - **Memory-First:** The database is the source of truth, not the LLM context window.
  - **Hardware Agnostic:** Runs on a Raspberry Pi 5 just as well as on a Threadripper workstation.
  - **Standardized:** Built 100% on the **Model Context Protocol (MCP)**.

### Project Value

**🏆 Why Jar-El Matters:**
Most "AI Assistants" are just chat interfaces with temporary memory. Jar-El is an **Operating System for your Life**. It separates **Compute** (replaceable) from **Context** (your most valuable asset). By self-hosting your semantic memory, you own your digital twin.

-----

## License 📜

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

-----

## Acknowledgments 🙏

Jar-El stands on the shoulders of giants:

  * **Anthropic**: For the Model Context Protocol (MCP) and the "Code Execution" paradigm.
  * **Qdrant**: For the high-performance Vector Database.
  * **IBM Docling**: For state-of-the-art document parsing.
  * **FastAPI**: For the robust backend infrastructure.

-----

## Citation & Research 📚

If you use Jar-El in your research, please cite:

```bibtex
@software{jarel2025,
  title={Jar-El: A Personal Semantic Operating System based on MCP and Self-Baking Memory},
  author={Engel, Prof. Dr. Mathias},
  year={2025},
  publisher={GitHub},
  url={[https://github.com/ProfEngel/Jar-El](https://github.com/ProfEngel/Jar-El)},
  note={Part-funded by MWK Baden-Württemberg and Stifterverband Deutschland}
}
```

-----

## Support the Project ☕

Jar-El is a passion project developed in my free time alongside my academic research.

If you find this tool useful and want to support the development (or just keep the coffee flowing during late-night coding sessions), I'd appreciate it\!

[](https://github.com/sponsors/ProfEngel)

-----

**Created by Prof. Dr. Mathias Engel 2024-2025**

*Made with ❤️ in Stuttgart, Germany*

-----

## About

Personal Semantic Operating System (S-OS) and Digital Twin Framework.

**Prof. Dr. Mathias Engel - ProfEngel** **Hochschule für Wirtschaft und Umwelt Nürtingen-Geislingen**

## Star History

<a href="https://star-history.com/#ProfEngel/Jar-El&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=ProfEngel/Jar-El&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=ProfEngel/Jar-El&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=ProfEngel/Jar-El&type=Date" />
 </picture>
</a>

### Topics

`mcp` `semantic-os` `digital-twin` `rag` `vector-database` `qdrant` `python` `docker` `ai-agent` `self-baking-memory` `personal-ai`

