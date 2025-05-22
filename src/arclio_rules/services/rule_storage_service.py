import os
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
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
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_org = os.environ.get("GITHUB_ORG", "arclio")
        self.base_temp_dir = Path(tempfile.gettempdir()) / "arclio-rules"
        self.base_temp_dir.mkdir(exist_ok=True)
        self.config = config
        logger.info(
            f"\nGitHub org: {self.github_org}"
            f"\nGitHub token: {self.github_token is not None}"
            f"\nBase temp dir: {self.base_temp_dir}"
        )

    async def init_client_repository(self, client_id: str, client_name: str):
        """Initialize a new client repository from template."""
        try:
            # Use GitHub API to create repo from template
            import requests

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            data = {
                "owner": self.github_org,
                "name": f"arclio-rules-client-{client_id}",
                "description": f"Rules repository for {client_name}",
                "private": True,
            }

            response = requests.post(
                f"https://api.github.com/repos/{self.github_org}/arclio-rules-template/generate",
                headers=headers,
                json=data,
            )

            if response.status_code == 201:
                return {"success": True}
            else:
                return {"success": False, "error": response.json()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_client_repo_path(self, client_id: str) -> Path:
        """Get the local path to a client's repository."""
        return self.base_temp_dir / f"client-{client_id}"

    def _ensure_repo_cloned(self, client_id: str) -> Repo:
        """Ensure the client repository is cloned locally."""
        repo_path = self._get_client_repo_path(client_id)

        # If repo exists, pull latest changes
        if repo_path.exists():
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
            return repo

        # Otherwise, clone the repo
        repo_url = f"https://{self.github_token}@github.com/{self.github_org}/arclio-rules-client-{client_id}.git"
        return Repo.clone_from(repo_url, repo_path)

    async def get_rule_content(self, client_id: str, rule_path: str) -> Dict[str, Any]:
        """Get the content of a rule from the repository."""
        try:
            # Try client repo first
            repo = self._ensure_repo_cloned(client_id)
            file_path = Path(repo.working_dir) / rule_path

            if file_path.exists():
                content = file_path.read_text()
                return {"success": True, "content": content}

            # If not found in client repo, try core repo
            core_repo_path = self.base_temp_dir / "core"
            if not core_repo_path.exists():
                core_repo_url = f"https://{self.github_token}@github.com/{self.github_org}/arclio-rules-core.git"
                core_repo = Repo.clone_from(core_repo_url, core_repo_path)
            else:
                core_repo = Repo(core_repo_path)
                core_repo.remotes.origin.pull()

            core_file_path = Path(core_repo.working_dir) / rule_path
            if core_file_path.exists():
                content = core_file_path.read_text()
                return {"success": True, "content": content}

            return {"success": False, "error": "Rule not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def save_rule_content(
        self,
        client_id: str,
        rule_path: str,
        content: str,
        commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a rule to the repository."""
        try:
            repo = self._ensure_repo_cloned(client_id)
            file_path = Path(repo.working_dir) / rule_path

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content to the file
            with open(file_path, "w") as f:
                f.write(content)

            # Add, commit and push
            repo.git.add(rule_path)
            repo.git.commit("-m", commit_message or f"Update {rule_path}")
            repo.git.push("origin", "main")

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_rules(self, client_id: str, directory: str = "") -> Dict[str, Any]:
        """List rules in a directory."""
        try:
            repo = self._ensure_repo_cloned(client_id)
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
                            "url": f"https://github.com/{self.github_org}/arclio-rules-client-{client_id}/blob/main/{relative_path}",
                        }
                    )

            return {"success": True, "rules": rules}

        except Exception as e:
            return {"success": False, "error": str(e)}
