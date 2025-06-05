import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import Repo
from loguru import logger
from pydantic import BaseModel


class RuleContent(BaseModel):
    content: str


class RuleSaveRequest(BaseModel):
    content: str
    commit_message: Optional[str] = None


class RuleMetadata(BaseModel):
    description: Optional[str] = None
    version: str = "1.0.0"
    owner: Optional[str] = None
    last_updated: Optional[str] = None
    applies_to: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class RuleStorageService:
    def __init__(self, config):
        """Initialize the RuleStorageService.

        Args:
            config (dict): Configuration dictionary containing necessary parameters.
        """
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is not set in environment variables.")
        self.github_org = os.environ.get("GITHUB_ORG")
        if not self.github_org:
            raise ValueError("GitHub organization is not set in environment variables.")
        self.repo_name = os.environ.get("REPO_NAME")
        if not self.repo_name:
            raise ValueError("Repo name is not set in environment variables.")
        self.repo_url = f"https://{self.github_token}@github.com/{self.github_org}/{self.repo_name}.git"  # noqa: E501
        self.base_temp_dir = Path(tempfile.gettempdir()) / "rules"
        self.base_temp_dir.mkdir(exist_ok=True)
        self.config = config

    def _get_client_repo_path(self) -> Path:
        """Get the local path to a client's repository."""
        return self.base_temp_dir

    def _ensure_repo_cloned(self) -> Repo:
        """Ensure the client repository is cloned locally."""
        repo_path = self._get_client_repo_path()
        logger.info(f"local repo path: {repo_path}")

        # If repo exists, pull latest changes
        if repo_path.exists():
            logger.info(f"repo path exists: {repo_path}")
            repo = Repo(repo_path)
            logger.info(f"repo to pull: {repo}")
            origin = repo.remotes.origin
            origin.pull()
            logger.info(f"Pulled latest changes from {self.repo_url} to {repo_path}")
            return repo

        # Otherwise, clone the repo
        logger.info(f"cloning repo: {self.repo_url} to {repo_path}")
        return Repo.clone_from(self.repo_url, repo_path, branch="main")

    async def get_rule_content(
        self, client_name: str, rule_path: str
    ) -> Dict[str, Any]:
        """Get the content of a rule from the repository."""
        try:
            # Try client repo first
            repo = self._ensure_repo_cloned()
            file_path = Path(repo.working_dir) / "rules" / client_name / rule_path
            logger.info(f"File path: {file_path}")

            if file_path.exists():
                content = file_path.read_text()
                return {"success": True, "content": content}

            return {"success": False, "error": "Rule not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_rules(self, directory: str = "") -> Dict[str, Any]:
        """List rules in a directory."""
        try:
            repo = self._ensure_repo_cloned()
            dir_path = Path(repo.working_dir) / directory

            if not dir_path.exists() or not dir_path.is_dir():
                return {"success": False, "error": "Directory not found"}

            rules = []

            for item in dir_path.iterdir():
                relative_path = str(item.relative_to(repo.working_dir))

                if item.is_dir():
                    rules.append(
                        {"name": item.name, "path": relative_path, "type": "dir"}
                    )
                elif item.suffix == ".mdc":
                    rules.append(
                        {
                            "name": item.name,
                            "path": relative_path,
                            "type": "file",
                            "sha": repo.git.rev_parse(f"HEAD:{relative_path}"),
                            "url": f"https://github.com/{self.github_org}/{self.repo_name}/blob/main/{relative_path}",  # noqa: E501
                        }
                    )

            return {"success": True, "rules": rules}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_rule_content(
        self,
        client_name: str,
        rule_path: str,
        content: str,
        commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a rule to the repository."""
        try:
            repo = self._ensure_repo_cloned()
            file_path = Path(repo.working_dir) / "rules" / client_name / rule_path

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content to the file
            with open(file_path, "w") as f:
                f.write(content)

            # Add, commit and push
            repo.git.add(f"rules/{client_name}/{rule_path}")
            repo.git.commit("-m", commit_message or f"Update {rule_path}")
            repo.git.push("origin", "main")

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
