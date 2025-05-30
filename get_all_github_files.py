import os
import argparse
from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException

def get_all_github_files(repo_name: str, branch: str = "main"):
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

    def get_all_file_paths(path: str = ""):
        files = []
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List all files in a GitHub repo branch.")
    parser.add_argument("--repo_name", type=str, required=True, help="GitHub repo name, e.g. owner/repo")
    parser.add_argument("--branch", type=str, default="main", help="Branch name (default: main)")
    args = parser.parse_args()

    try:
        files = get_all_github_files(args.repo_name, args.branch)
        for f in files:
            print(f)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

