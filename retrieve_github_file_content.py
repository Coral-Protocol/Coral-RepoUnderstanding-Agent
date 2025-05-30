import os
import sys
import argparse
from github import Github, GithubException, ContentFile

def retrieve_github_file_content(repo_name: str, file_path: str, branch: str = "main") -> str:
    """
    Retrieve the content of a specific file from a specific branch of a GitHub repository.

    Args:
        repo_name (str): Full repository name in the format "owner/repo".
        file_path (str): Path to the file in the repository.
        branch (str): Branch name to retrieve the file from. Defaults to "main".

    Returns:
        str: The decoded content of the file.

    Raises:
        ValueError: If GITHUB_ACCESS_TOKEN is not set.
        GithubException: On repository access or API failure.
        ValueError: If multiple files are returned (e.g., by mistake).
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable is not set.")

    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GithubException(f"Failed to access repository '{repo_name}': {e.data}")

    try:
        file_content = repo.get_contents(file_path, ref=branch)
    except GithubException as e:
        raise GithubException(f"Failed to get content of file '{file_path}' in branch '{branch}': {e.data}")

    if isinstance(file_content, list):
        raise ValueError("Multiple files returned; the path may refer to a directory, not a file.")
    return file_content.decoded_content.decode()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve GitHub file content.")
    parser.add_argument("--repo_name", type=str, required=True, help="Repository name in 'owner/repo' format")
    parser.add_argument("--file_path", type=str, required=True, help="Path to the file inside the repo")
    parser.add_argument("--branch", type=str, default="main", help="Branch name (default: main)")
    args = parser.parse_args()

    try:
        result = retrieve_github_file_content(args.repo_name, args.file_path, args.branch)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
