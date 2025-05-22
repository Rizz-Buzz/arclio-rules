from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from src.arclio_rules.services.rule_indexing_service import RuleIndexingService
from src.arclio_rules.services.rule_resolution_service import RuleResolutionService
from src.arclio_rules.services.rule_storage_service import (
    RuleSaveRequest,
    RuleStorageService,
)

router = APIRouter(prefix="/api/rules")
rule_storage_service = RuleStorageService(config={})
rule_indexing_service = RuleIndexingService(config={})
rule_resolution_service = RuleResolutionService(config={})


class ApplyRulesRequest(BaseModel):
    rule_paths: List[str]
    current_context: Optional[str] = ""


# Get a rule
@router.get("/{client_id}/{rule_path:path}")
async def get_rule(client_id: str, rule_path: str):
    """Get a rule from the client repository using the provided client ID and rule path.

    This function fetches the rule content from the storage service and returns it.
    If the rule is not found, it raises an HTTPException with a 404 status code.

    Args:
        client_id (str): The ID of the client whose rule is being fetched.
        rule_path (str): The path to the rule in the client's repository.

    Raises:
        HTTPException: If the rule is not found, a 404 error is raised.
        HTTPException: If the rule content cannot be retrieved, a 500 error is raised.

    Returns:
        dict: A dictionary containing the success status and the rule content.
    """
    logger.info(
        f"Fetching rule from client repo: '{client_id}', and path: '{rule_path}'"
    )
    result = await rule_storage_service.get_rule_content(client_id, rule_path)

    if result["success"]:
        return {"success": True, "content": result["content"]}
    else:
        logger.error(f"Failed to get rule: {result.get('error')}")
        raise HTTPException(status_code=404, detail="Rule not found")


# Save a rule
@router.post("/{client_id}/{rule_path:path}")
async def save_rule(client_id: str, rule_path: str, request: RuleSaveRequest):
    """Save a rule to the client repository.

    This function saves the rule content to the specified path in the client's
    repository. It also indexes the rule after saving.
    If the content is empty, it raises an HTTPException with a 400 status code.
    If the save operation fails, it raises an HTTPException with a 500 status code.
    If the save operation is successful, it returns a success message.

    Args:
        client_id (str): The ID of the client whose rule is being saved.
        rule_path (str): The path to save the rule in the client's repository.
        request (RuleSaveRequest): The request object containing the rule content

    Raises:
        HTTPException: If the content is empty, a 400 error is raised.
        HTTPException: If the save operation fails, a 500 error is raised.

    Returns:
        dict: A dictionary containing the success status.
    """
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")

    result = await rule_storage_service.save_rule_content(
        client_id, rule_path, request.content, request.commit_message
    )

    if result["success"]:
        # Index the rule after saving
        await rule_indexing_service.index_rule(client_id, rule_path)
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to save rule")


# List rules in a directory
@router.get("/{client_id}/list/{directory:path}")
async def list_rules(client_id: str, directory: Optional[str] = ""):
    """List rules in a directory within the client repository.

    This function retrieves the list of rules from the specified directory
    in the client's repository. If the directory is not specified, it defaults
    to the root directory.

    Args:
        client_id (str): The ID of the client whose rules are being listed.
        directory (str, optional): The directory path to list rules from.
            Defaults to an empty string, which represents the root directory.

    Raises:
        HTTPException: If the list operation fails, a 500 error is raised.

    Returns:
        dict: A dictionary containing the success status and the list of rules.
    """
    result = await rule_storage_service.list_rules(client_id, directory)

    if result["success"]:
        return {"success": True, "rules": result["rules"]}
    else:
        raise HTTPException(status_code=500, detail="Failed to list rules")


# Search rules
@router.get("/{client_id}/search")
async def search_rules(
    client_id: str,
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
):
    """Search for rules in the client repository using a query string.

    This function uses the rule indexing service to perform a search

    Args:
        client_id (str): The ID of the client whose rules are being searched.
        q (str, optional): The search query string to find matching rules.
            Defaults to Query(..., description="Search query").
        limit (int, optional): The maximum number of results to return.
            Defaults to Query(10, ge=1, le=100).

    Raises:
        HTTPException: If the query is empty, a 400 error is raised.
        HTTPException: If the search operation fails, a 500 error is raised.

    Returns:
        dict: A dictionary containing the success status and the search results.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query is required")

    result = await rule_indexing_service.search_rules(client_id, q, limit)

    if result["success"]:
        return {"success": True, "results": result["results"]}
    else:
        raise HTTPException(status_code=500, detail="Search failed")


# Apply rules to context
@router.post("/{client_id}/apply")
async def apply_rules(client_id: str, request: ApplyRulesRequest):
    """Apply rules to provide context for AI.

    This function takes a list of rule paths and the current context,
    applies the rules to enhance the context, and returns the enhanced context.
    If the rule paths array is empty, it raises an HTTPException with a 400 status code.
    If the application of rules fails, it raises an HTTPException with a 500 status code.
    If the application of rules is successful, it returns a success message and the enhanced context.

    Raises:
        HTTPException: If the rule paths array is empty, a 400 error is raised.
        HTTPException: If the application of rules fails, a 500 error is raised.

    Args:
        client_id (str): The ID of the client whose rules are being applied.
        request (ApplyRulesRequest): The request object containing rule paths and current context.
    """  # noqa: E501
    if not request.rule_paths:
        raise HTTPException(status_code=400, detail="Rule paths array is required")

    try:
        enhanced_context = await rule_resolution_service.apply_rules_to_context(
            client_id, request.rule_paths, request.current_context
        )

        return {"success": True, "context": enhanced_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
