import base64
import os
from functools import lru_cache
from typing import Dict, List, Optional

import requests
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel


class RuleContent(BaseModel):
    company_name: str
    category_name: str
    rule_name: str
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


class RuleFetchService:
    """Service to fetch and manage rules from a GitHub repository."""

    def __init__(self, config):
        """Initialize the RuleFetchService with configuration parameters.

        Args:
            config (dict): Configuration dictionary containing necessary parameters.
        """
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is not set in environment variables.")
        self.github_org = os.environ.get("GITHUB_ORG")
        if not self.github_org:
            raise ValueError("GitHub organization is not set in environment variables.")
        self.rules_repo_name = os.environ.get("RULES_REPO_NAME")
        if not self.rules_repo_name:
            raise ValueError("Rules repo name is not set in environment variables.")
        self.gh_rules_repo = f"https://api.github.com/repos/{self.github_org}/{self.rules_repo_name}/contents"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.config = config

    # In-memory cache for GitHub API responses
    @lru_cache(maxsize=1000)
    def fetch_github_content(self, path: str) -> Dict:
        """Fetch content from GitHub API with error handling.

        Args:
            path (str): The path to the content in the GitHub repository.

        Returns:
            Dict: The JSON response from the GitHub API.
        """
        try:
            url = f"{self.gh_rules_repo}/{path}"
            logger.info(f"Fetching content from GitHub: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to fetch {path}: {e.response.json()}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to fetch {path}: {e.response.json().get('message', 'Unknown error')}",  # noqa: E501
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching {path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

    def list_all_companies(self) -> List[str]:
        """List all company directories under rules/.

        Returns:
            List[str]: A list of company names (directory names) under rules/.
        """
        try:
            content = self.fetch_github_content("rules")
            companies = [
                item["name"]
                for item in content
                if item["type"] == "dir" and item["name"] != "index.mdc"
            ]
            return companies
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error listing companies: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to list companies")

    def list_company_categories(self, company: str) -> List[str]:
        """List all categories for a specific company.

        Args:
            company (str): The name of the company whose categories are being listed.

        Returns:
            List[str]: A list of category names for the specified company.
        """
        path = f"rules/{company}"
        try:
            content = self.fetch_github_content(path)
            if isinstance(content, dict) and content.get("type") == "file":
                raise HTTPException(
                    status_code=404, detail=f"Company {company} is not a directory"
                )
            categories = [item["name"] for item in content if item["type"] == "dir"]
            return categories
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error listing categories for {company}: {str(e)}")
            raise HTTPException(
                status_code=404, detail=f"Failed to list categories for {company}"
            )

    def list_category_rules(self, company: str, category: str) -> List[str]:
        """List all .mdc rules in a specific company category.

        Args:
            company (str): The name of the company whose category rules are being listed.
            category (str): The name of the category whose rules are being listed.

        Returns:
            List[str]: A list of rule names (without .mdc extension) in the specified category.
        """  # noqa: E501
        path = f"rules/{company}/{category}"
        try:
            content = self.fetch_github_content(path)
            if isinstance(content, dict) and content.get("type") == "file":
                raise HTTPException(
                    status_code=404, detail=f"Category {category} is not a directory"
                )
            rules = [
                item["name"].replace(".mdc", "")
                for item in content
                if item["type"] == "file" and item["name"].endswith(".mdc")
            ]
            return rules
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error listing rules for {company}/{category}: {str(e)}")
            raise HTTPException(
                status_code=404, detail=f"Failed to list rules for {company}/{category}"
            )

    def get_rule(
        self,
        company: str,
        category: str,
        rule: str,
        is_main_rule: bool = False,
    ) -> dict:
        """Fetch the content of a specific .mdc rule file.

        Args:
            company (str): The name of the company whose rule is being fetched.
            category (str): The category of the rule.
            rule (str): The name of the rule (without .mdc extension).
            is_main_rule (bool): Whether the rule is the main rule (index.mdc).
                If True, fetches from rules/index.mdc.

        Returns:
            Dict: A dictionary containing the rule content and metadata.
        """
        try:
            if is_main_rule:
                path = "rules/index.mdc"
            else:
                path = f"rules/{company}/{category}/{rule}.mdc"
            content = self.fetch_github_content(path)
            if content.get("type") != "file":
                raise HTTPException(
                    status_code=404, detail=f"Rule {rule}.mdc is not a file"
                )
            decoded_content = base64.b64decode(content["content"]).decode("utf-8")
            return {
                "company": company,
                "category": category,
                "rule": rule,
                "content": decoded_content,
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                f"Error fetching rule {rule}.mdc for {company}/{category}: {str(e)}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch rule {rule}.mdc for {company}/{category}",
            )
