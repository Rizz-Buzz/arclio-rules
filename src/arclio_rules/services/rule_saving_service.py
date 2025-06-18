import base64
import os

import requests
from fastapi import HTTPException
from loguru import logger


class RuleSavingService:
    """Service to save rules to a GitHub repository."""

    def __init__(self):
        """Initialize the RuleSavingService with GitHub configuration."""
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is not set in environment variables.")
        self.github_org = os.environ.get("GITHUB_ORG")
        if not self.github_org:
            raise ValueError("GitHub organization is not set in environment variables.")
        self.rules_repo_name = os.environ.get("RULES_REPO_NAME")
        if not self.rules_repo_name:
            raise ValueError("Rules repo name is not set in environment variables.")
        self.gh_rules_repo = f"https://api.github.com/repos/{self.github_org}/{self.rules_repo_name}/contents"  # noqa: E501
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _get_file_sha(self, path: str) -> str | None:
        """Get the SHA of an existing file if it exists.

        Args:
            path (str): The path to the file in the GitHub repository.

        Returns:
            str | None: The SHA of the file if it exists, None otherwise.
        """
        try:
            url = f"{self.gh_rules_repo}/{path}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("sha")
            return None
        except requests.exceptions.RequestException:
            return None

    def save_rule(
        self, company: str, category: str, rule: str, content: str
    ) -> dict[str, str]:
        """Save a rule to GitHub.

        Args:
            company (str): The name of the company (will be used as folder name).
            category (str): The category of the rule (will be used as subfolder name).
            rule (str): The name of the rule (without .mdc extension).
            content (str): The content of the rule file.

        Returns:
            dict[str, str]: A dictionary containing the status and path of the saved rule.

        Raises:
            HTTPException: If there's an error saving the rule.
        """  # noqa: E501
        # Validate inputs
        if not all([company, category, rule, content]):
            raise HTTPException(
                status_code=400,
                detail="Company, category, rule name, and content are required",
            )

        # Ensure rule has .mdc extension
        if not rule.endswith(".mdc"):
            rule = f"{rule}.mdc"

        # Construct the file path
        file_path = f"rules/{company}/{category}/{rule}"

        try:
            # Get the SHA if file exists (needed for updating)
            file_sha = self._get_file_sha(file_path)

            # Prepare the request data
            data = {
                "message": f"Update rule: {file_path}",
                "content": base64.b64encode(content.encode()).decode(),
            }

            if file_sha:
                data["sha"] = file_sha
                logger.info(f"Updating existing rule at {file_path}")
            else:
                logger.info(f"Creating new rule at {file_path}")

            # Make the API request
            url = f"{self.gh_rules_repo}/{file_path}"
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()

            return {
                "status": "success",
                "path": file_path,
                "action": "updated" if file_sha else "created",
            }

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("message", str(e))
            logger.error(f"GitHub API error while saving rule: {error_detail}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to save rule: {error_detail}",
            )
        except Exception as e:
            logger.error(f"Unexpected error while saving rule: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error while saving rule: {str(e)}",
            )
