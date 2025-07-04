## [Repo Understanding Agent](https://github.com/Coral-Protocol/Coral-Pandas-Agent)
 
The RepoUnderstanding Agent can help you automatically analyze any GitHub repository by comprehensively reading key files (such as README.md, source code, and configuration files) and summarizing the repository's purpose, main modules, usage instructions, and architecture.

![Agentimage](https://github.com/Coral-Protocol/awesome-agents-for-multi-agent-systems/blob/main/images/Coral-RepoUnderstanding-Agent.png)

## Responsibility

The RepoUnderstanding Agent systematically inspects the most important files in a repository and delivers a clear, concise overview of the project structure and functionality.

## Details
- **Framework**: LangChain
- **Tools used**: PyGithub List File Tool, PyGithub Read File Tool, Coral Server Tools
- **AI model**: OpenAI GPT-4.1
- **Date added**: 02/05/25
- **License**: MIT

## Setup the Agent

### 1. Clone & Install Dependencies

<details>  

```bash
# In a new terminal clone the repository:
git clone https://github.com/Coral-Protocol/Coral-RepoUnderstanding-Agent.git

# Navigate to the project directory:
cd Coral-RepoUnderstanding-Agent

# Download and run the UV installer, setting the installation directory to the current one
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=$(pwd) sh

# Create a virtual environment named `.venv` using UV
uv venv .venv

# Activate the virtual environment
source .venv/bin/activate

# install uv
pip install uv

# Install dependencies from `pyproject.toml` using `uv`:
uv sync
```

</details>

### 2. Configure Environment Variables

Get the API Keys:
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [GitHub Personal Access Token](https://github.com/settings/tokens)

<details>

```bash
# Create .env file in project root
cp -r .env.example .env
```
</details>

## Run the Agent

You can run in either of the below modes to get your system running.  

- The Executable Model is part of the Coral Protocol Orchestrator which works with [Coral Studio UI](https://github.com/Coral-Protocol/coral-studio).  
- The Dev Mode allows the Coral Server and all agents to be seaprately running on each terminal without UI support.  

### 1. Executable Mode

Checkout: [How to Build a Multi-Agent System with Awesome Open Source Agents using Coral Protocol](https://github.com/Coral-Protocol/existing-agent-sessions-tutorial-private-temp) and update the file: `coral-server/src/main/resources/application.yaml` with the details below, then run the [Coral Server](https://github.com/Coral-Protocol/coral-server) and [Coral Studio UI](https://github.com/Coral-Protocol/coral-studio). You do not need to set up the `.env` in the project directory for running in this mode; it will be captured through the variables below.

<details>

For Linux or MAC:

```bash
# PROJECT_DIR="/PATH/TO/YOUR/PROJECT"

applications:
  - id: "app"
    name: "Default Application"
    description: "Default application for testing"
    privacyKeys:
      - "default-key"
      - "public"
      - "priv"

registry:
  repo_understanding_agent:
    options:
      - name: "API_KEY"
        type: "string"
        description: "API key for the service"
      - name: "GITHUB_ACCESS_TOKEN"
        type: "string"
        description: "key for the github service"
    runtime:
      type: "executable"
      command: ["bash", "-c", "${PROJECT_DIR}/run_agent.sh main.py"]
      environment:
        - name: "API_KEY"
          from: "API_KEY"
        - name: "GITHUB_ACCESS_TOKEN"
          from: "GITHUB_ACCESS_TOKEN"
        - name: "MODEL_NAME"
          value: "gpt-4.1"
        - name: "MODEL_PROVIDER"
          value: "openai"
        - name: "MODEL_TOKEN"
          value: "16000"
        - name: "MODEL_TEMPERATURE"
          value: "0.3"

```

For Windows, create a powershell command (run_agent.ps1) and run:

```bash
command: ["powershell","-ExecutionPolicy", "Bypass", "-File", "${PROJECT_DIR}/run_agent.ps1","main.py"]
```

</details>

### 2. Dev Mode

Ensure that the [Coral Server](https://github.com/Coral-Protocol/coral-server) is running on your system and run below command in a separate terminal.

<details>

```bash
# Run the agent using `uv`:
uv run python main.py
```
</details>


## Example

<details>


```bash
# Input:
Please give me a comprehensive instruction of the master branch of Coral-Protocol/coral-server.

# Output:
Here is a comprehensive overview of the master branch of the Coral-Protocol/coral-server repository:

**Project Purpose & Main Functionality:**
- Coral Server implements the Coral Protocol, acting as a Model Context Protocol (MCP) server that enables communication between AI agents via a thread-based messaging system.
- It provides tools for agents to register, create/manage threads, send messages, mention other agents, and receive notifications when mentioned.
- The server is designed to facilitate multi-agent collaboration, with a focus on composability, scalability, and secure agent communication.

**Primary Components/Modules:**
- **src/main/kotlin/org/coralprotocol/coralserver/**: Core server logic, including the entry point (`Main.kt`), server setup (`CoralServer.kt`), session management, and orchestrator for agent lifecycle.
- **mcptools/**: Implements the MCP tools (e.g., list_agents, create_thread, add/remove participants, send_message, wait_for_mentions) that agents use to interact.
- **routes/**: Defines HTTP/SSE endpoints for agent and session communication.
- **orchestrator/**: Handles agent registration, spawning, and lifecycle management.
- **examples/camel-search-maths/**: Provides a practical example of multi-agent collaboration using the server with CAMEL agents.
- **application.yaml**: Configures applications and agent registry (including how agents are orchestrated and their environment variables).

**How to Use/Run the Project:**
- The server can be run via Gradle (`./gradlew run`) or as a standalone JAR after building.
- Supports multiple modes: standard I/O, SSE server (default, port 5555), and development mode.
- Agents connect to the server and use the available MCP tools for communication.
- Example workflow: Start the server, then run the example agents (math, search, interface) in the example directory. The agents collaborate to answer user queries.

**Noteworthy Implementation Details:**
- Built in Kotlin, using Ktor for the server and SSE/WebSocket support.
- Extensible agent registry and orchestrator allow for local and (planned) remote agent management.
- YAML-based configuration for applications and agent orchestration.
- Designed for open, composable AI agent societies, with a focus on secure, scalable, and flexible communication.
- Early-stage project with ongoing development toward remote mode and expanded features.

**Summary:**
Coral Server is a foundation for multi-agent AI systems, enabling agents to communicate, collaborate, and manage conversations through a standardized protocol and set of tools. It is highly extensible and intended as open infrastructure for the "Society of AI Agents." The project is not yet production-ready but provides a robust starting point for building complex agent-based systems.
```
</details>


## Creator Details
- **Name**: Xinxing
- **Affiliation**: Coral Protocol
- **Contact**: [Discord](https://discord.com/invite/Xjm892dtt3)
