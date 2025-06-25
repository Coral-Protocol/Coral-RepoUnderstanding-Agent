## [Coral RepoUnderstanding Agent](https://github.com/Coral-Protocol/Coral-RepoUnderstanding-Agent)

The RepoUnderstanding Agent can help you automatically analyze any GitHub repository by comprehensively reading key files (such as README.md, source code, and configuration files) and summarizing the repository's purpose, main modules, usage instructions, and architecture.

## Responsibility
The RepoUnderstanding Agent systematically inspects the most important files in a repository and delivers a clear, concise overview of the project structure and functionality.

## Details
- **Framework**: LangChain
- **Tools used**: PyGithub List File Tool, PyGithub Read File Tool, Coral Server Tools
- **AI model**: OpenAI GPT-4.1
- **Date added**: 02/05/25

- **License**: MIT

## Use the Agent in Orchestration
Get the API Keys:
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [GitHub Personal Access Token](https://github.com/settings/tokens)

### Executable Agent Definition 
```yaml
  coral-repo:
    options:
      - name: "OPENAI_API_KEY"
        type: "string"
        description: "OpenAI API Key for RepoUnderstanding Agent"
      - name: "GITHUB_ACCESS_TOKEN"
        type: "string"
        description: "GitHub Access Token"
    runtime:
      type: "executable"
      command:
        [
          "bash",
          "-c",
          "cd ../Coral-RepoUnderstanding-Agent && uv sync && uv run 4-langchain-RepoUnderstandingAgent.py",
        ]
      environment:
        - name: "OPENAI_API_KEY"
          from: "OPENAI_API_KEY"
        - name: "GITHUB_ACCESS_TOKEN"
          from: "GITHUB_ACCESS_TOKEN"
```
### Docker Agent Definition 

```yaml
  repounderstanding:
    options:
      - name: "OPENAI_API_KEY"
        type: "string"
        description: "OpenAI API Key"
      - name: "GITHUB_ACCESS_TOKEN"
        type: "string"
        description: "GitHub Access Token"
    runtime:
      type: "docker"
      image: "coralprotocol/coral-repounderstanding:latest"
      environment:
        - name: "OPENAI_API_KEY"
          from: "OPENAI_API_KEY"
        - name: "GITHUB_ACCESS_TOKEN"
          from: "GITHUB_ACCESS_TOKEN"
```

## Use the Agent  

### 1. Clone & Install Dependencies


<details>  

Ensure that the [Coral Server](https://github.com/Coral-Protocol/coral-server) is running on your system and the [Interface Agent](https://github.com/Coral-Protocol/Coral-Interface-Agent) is running on the Coral Server.  

<details>
  
<summary>Click to expand setup instructions in normal way</summary>

```bash
# Clone the RepoUnderstanding Agent repository
git clone https://github.com/Coral-Protocol/Coral-RepoUnderstanding-Agent.git

# Navigate to the project directory
cd Coral-RepoUnderstanding-Agent

# Install `uv`:
pip install uv

# Install dependencies from `pyproject.toml` using `uv`:
uv sync
```
This command will read the `pyproject.toml` file and install all specified dependencies in a virtual environment managed by `uv`.

</details>


<details>
  
<summary>Click to expand setup instructions with docker</summary>

```bash
# Clone the RepoUnderstanding Agent repository
git clone https://github.com/Coral-Protocol/Coral-RepoUnderstanding-Agent.git

# Navigate to the project directory
cd Coral-RepoUnderstanding-Agent

docker pull coralprotocol/coral-repounderstanding
```
</details>

</details>

### 2. Configure Environment Variables
<details>

Get the API Keys:
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [GitHub Personal Access Token](https://github.com/settings/tokens)

Create a .env file in the project root:
```bash
cp -r .env.example .env
```

Add your API keys and any other required environment variables to the .env file.

Required environment variables:
- `OPENAI_API_KEY`
- `GITHUB_ACCESS_TOKEN`






</details>

### 3. Run Agent
<details>
  
<details>
  
<summary>Run the agent using uv</summary>

```bash
uv run 4-langchain-RepoUnderstandingAgent.py
```
</details>

<details>

<summary>Run the agent using docker</summary>

```bash
docker run --network host --env-file .env -it coralprotocol/coral-repounderstanding
```
</details>

</details>

### 4. Example
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
