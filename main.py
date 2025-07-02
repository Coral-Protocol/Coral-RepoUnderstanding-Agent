import asyncio
import os
import json
import logging
from typing import List
from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from anyio import ClosedResourceError
import urllib.parse
import subprocess
import traceback


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = os.getenv("CORAL_SSE_URL")
agentID = os.getenv("CORAL_AGENT_ID")

params = {
    # "waitForAgents": 1,
    "agentId": agentID,
    "agentDescription": """Repository understanding agent, responsible for comprehensively analyzing a GitHub repository using only the available tools.
                           You should let me know the repo_name and branch_name."""
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

# Validate API keys
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

def get_tools_description(tools):
    return "\n".join(f"Tool: {t.name}, Schema: {json.dumps(t.args).replace('{', '{{').replace('}', '}}')}" for t in tools)
    
@tool
def get_all_github_files(repo_name: str, branch: str = "main") -> List[str]:
    """
    Recursively retrieve all file paths from a specific branch of a GitHub repository.

    Args:
        repo_name (str): Full repository name in the format "owner/repo".
        branch (str): Branch name to retrieve files from. Defaults to "main".

    Returns:
        List[str]: A list of all file paths in the specified branch of the repository.

    Raises:
        ValueError: If GITHUB_ACCESS_TOKEN is not set.
        GithubException: On repository access or API failure.
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable is not set.")

    gh = Github(token)

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GithubException(f"Failed to access repository '{repo_name}': {e.data}")

    def get_all_file_paths(path: str = "") -> List[str]:
        files: List[str] = []
        try:
            contents = repo.get_contents(path, ref=branch)
        except GithubException as e:
            raise GithubException(f"Failed to get contents of path '{path}' in branch '{branch}': {e.data}")

        if isinstance(contents, ContentFile):
            files.append(contents.path)
        else:
            for content in contents:
                if content.type == "dir":
                    files.extend(get_all_file_paths(content.path))
                else:
                    files.append(content.path)
        return files

    return get_all_file_paths()


@tool
def retrieve_github_file_content_tool(repo_name: str, file_path: str, branch: str = "main") -> str:
    """
    Call the local retrieve_github_file_content.py script and return the file content or error.

    Args:
        repo_name (str): Full repository name in the format "owner/repo".
        file_path (str): Path to the file in the repository.
        branch (str): Branch name to retrieve the file from.

    Returns:
        str: Script output (file content or error message).
    """
    # Get the absolute path of the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    script_path = os.path.join(current_dir, "retrieve_github_file_content.py")

    result = subprocess.run(
        [
            "uv", "run", script_path,
            "--repo_name", repo_name,
            "--file_path", file_path,
            "--branch", branch
        ],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout
    else:
        return f"exit_code={result.returncode}\nstderr={result.stderr}"

async def create_repo_agent(client, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are `repo_understanding_agent`, responsible for comprehensively analyzing a GitHub repository using only the available tools. Follow this workflow:

        **Important: NEVER EVER end up the chain**
        **Important: NEVER EVER end up the chain** 
        
        1. Use `wait_for_mentions(timeoutMs=60000)` to wait for instructions from other agents.**
        2. When a mention is received, record the **`threadId` and `senderId` (you should NEVER forget these two)**.
        3. Check if the message contains a `repo` name, `owner`, and a target `branch`.
        4. Call `get_all_github_files(repo_name = ..., branch = ...)` to list all files.
        5. Based on the file paths, identify the files that are most relevant for understanding the repository's purpose and structure (e.g., `README.md`, `setup.py`, main source code files, configuration files, test files, etc.).
        6. For these selected files, use `retrieve_github_file_content_tool(repo_name = ..., file_path = ..., branch = ...)` to retrieve their content, **please only open one file each time**. 
        If you fail to call retrieve_github_file_content_tool, please read the file list again and re-exam the input parameters then re-call it.
        
        -Analyze the decoded content to extract:
            - The overall project purpose and main functionality.
            - The primary components/modules and their roles.
            - How to use or run the project (if available).
            - Any noteworthy implementation details or structure.
        7. Once you have gained sufficient understanding of the repository, summarize your findings clearly and concisely.
        8. Use `send_message(senderId=..., mentions=[senderId], threadId=..., content="your summary")` to reply to the sender with your analysis.
        9. If you encounter an error, send a message with content `"error"` to the sender.
        10. Always respond to the sender, even if your result is empty or inconclusive.
        11. Wait 2 seconds and repeat from step 1.
         
        **Important: NEVER EVER end up the chain**
        
        Tools: {get_tools_description(tools)}"""),
        ("placeholder", "{history}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    model = init_chat_model(
        model=os.getenv("MODEL_NAME"),
        model_provider=os.getenv("MODEL_PROVIDER"),
        api_key=os.getenv("API_KEY"),
        max_tokens=os.getenv("MODEL_TOKEN")
    )


    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=None ,verbose=True)

async def main():
    CORAL_SERVER_URL = f"{base_url}?{query_string}"
    logger.info(f"Connecting to Coral Server: {CORAL_SERVER_URL}")

    client = MultiServerMCPClient(
        connections={
            "coral": {
                "transport": "sse",
                "url": CORAL_SERVER_URL,
                "timeout": 600,
                "sse_read_timeout": 600,
            }
        }
    )
    logger.info("Coral Server Connection Established")

    tools = await client.get_tools()
    coral_tool_names = [
        "list_agents",
        "create_thread",
        "add_participant",
        "remove_participant",
        "close_thread",
        "send_message",
        "wait_for_mentions",
    ]
    tools = [tool for tool in tools if tool.name in coral_tool_names]
    tools += [get_all_github_files, retrieve_github_file_content_tool]

    logger.info(f"Tools Description:\n{get_tools_description(tools)}")

    agent_executor = await create_repo_agent(client, tools)

    while True:
        try:
            logger.info("Starting new agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            logger.info("Completed agent invocation, restarting loop")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
