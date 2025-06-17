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
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_community.callbacks import get_openai_callback
from langchain.memory import ConversationSummaryMemory
from langchain_core.memory import BaseMemory
from dotenv import load_dotenv
from anyio import ClosedResourceError
import urllib.parse
import subprocess


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = os.getenv("CORAL_SERVER_URL")
params = {
    "waitForAgents": 1,
    "agentId": "repo_understanding_agent",
    "agentDescription": """I am `repo_understanding_agent`, responsible for comprehensively analyzing a GitHub repository using only the available tools.
                           You should let me know the repo_name and branch_name."""
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"
AGENT_NAME = "codediff_review_agent"

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

class HeadSummaryMemory(BaseMemory):
    def __init__(self, llm, head_n=3):
        super().__init__()
        self.head_n = head_n
        self._messages = []
        self.summary_memory = ConversationSummaryMemory(llm=llm)

    def save_context(self, inputs, outputs):
        user_msg = inputs.get("input") or next(iter(inputs.values()), "")
        ai_msg = outputs.get("output") or next(iter(outputs.values()), "")
        self._messages.append({"input": user_msg, "output": ai_msg})
        if len(self._messages) > self.head_n:
            self.summary_memory.save_context(inputs, outputs)

    def load_memory_variables(self, inputs):
        messages = []
        
        for i in range(min(self._head_n, len(self._messages))):
            msg = self._messages[i]
            messages.append(HumanMessage(content=msg['input']))
            messages.append(AIMessage(content=msg['output']))
        # summary
        if len(self._messages) > self._head_n:
            summary_var = self.summary_memory.load_memory_variables(inputs).get("history", [])
            if summary_var:
                
                if isinstance(summary_var, str):
                    messages.append(HumanMessage(content="[Earlier Summary]\n" + summary_var))
                elif isinstance(summary_var, list):
                    messages.extend(summary_var)
        return {"history": messages}

    def clear(self):
        self._messages.clear()
        self.summary_memory.clear()

    @property
    def memory_variables(self):
        return {"history"}
    
    @property
    def head_n(self):
        return self._head_n

    @head_n.setter
    def head_n(self, value):
        self._head_n = value

    @property
    def summary_memory(self):
        return self._summary_memory

    @summary_memory.setter
    def summary_memory(self, value):
        self._summary_memory = value

async def create_codediff_review_agent(client, tools):
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

    model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=32768
    )

    '''model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3
    )'''

    memory = HeadSummaryMemory(llm=model, head_n=4)


    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, memory=memory, max_iterations=100 ,verbose=True)

async def main():
    max_retries = 5
    retry_delay = 5  # seconds

    github_token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable is required")

    for attempt in range(max_retries):
        client = None
        try:
            client = MultiServerMCPClient(
                connections={
                    "coral": {
                        "transport": "sse",
                        "url": MCP_SERVER_URL,
                        "timeout": 600,
                        "sse_read_timeout": 600,
                    }
                }
            )
            logger.info(f"Initialized MultiServerMCPClient to {MCP_SERVER_URL}")

            tools = await client.get_tools()
            coral_tool_names = [
                "list_agents", "create_thread", "add_participant",
                "remove_participant", "close_thread", "send_message",
                "wait_for_mentions",
            ]
            tools = [t for t in tools if t.name in coral_tool_names]
            tools += [get_all_github_files, retrieve_github_file_content_tool]

            logger.info(f"Tools Description:\n{get_tools_description(tools)}")

            with get_openai_callback() as cb:
                agent_executor = await create_codediff_review_agent(client, tools)
                await agent_executor.ainvoke({})
                logger.info("Token usage:")
                logger.info(f"  Prompt Tokens: {cb.prompt_tokens}")
                logger.info(f"  Completion Tokens: {cb.completion_tokens}")
                logger.info(f"  Total Tokens: {cb.total_tokens}")
                logger.info(f"  Total Cost (USD): ${cb.total_cost:.6f}")

            break

        except ClosedResourceError as e:
            logger.error(f"ClosedResourceError on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise

if __name__ == "__main__":
    asyncio.run(main())
