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
@router.get(
    "/{client_id}/{rule_path:path}",
    operation_id="get_rule",
)
async def get_rule(client_id: str, rule_path: str):
    """Get a rule from the client repository using the provided client ID and rule path.
    This function fetches the rule content from the storage service and returns it.
    If the rule is not found, it raises an HTTPException with a 404 status code.

    Args:
        client_id (str): The ID of the client whose rule is being fetched.
        rule_path (str): The path to the rule in the client's repository.

    Raises:
        HTTPException: If the rule is not found, a 404 error is raised.

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
@router.post(
    "/{client_id}/{rule_path:path}",
    # operation_id="save_rule_for_client_from_path",
)
async def save_rule(client_id: str, rule_path: str, request: RuleSaveRequest):
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
@router.get(
    "/{client_id}/list/{directory:path}",
    # operation_id="list_rules_for_client_in_directory",
)
async def list_rules(client_id: str, directory: Optional[str] = ""):
    result = await rule_storage_service.list_rules(client_id, directory)

    if result["success"]:
        return {"success": True, "rules": result["rules"]}
    else:
        raise HTTPException(status_code=500, detail="Failed to list rules")


# Search rules
@router.get(
    "/{client_id}/search",
    # operation_id="search_rules_for_client",
)
async def search_rules(
    client_id: str,
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
):
    if not q:
        raise HTTPException(status_code=400, detail="Query is required")

    result = await rule_indexing_service.search_rules(client_id, q, limit)

    if result["success"]:
        return {"success": True, "results": result["results"]}
    else:
        raise HTTPException(status_code=500, detail="Search failed")


# Apply rules to context
@router.post(
    "/{client_id}/apply",
    # operation_id="apply_rules_to_context_for_client",
)
async def apply_rules(client_id: str, request: ApplyRulesRequest):
    if not request.rule_paths:
        raise HTTPException(status_code=400, detail="Rule paths array is required")

    try:
        enhanced_context = await rule_resolution_service.apply_rules_to_context(
            client_id, request.rule_paths, request.current_context
        )

        return {"success": True, "context": enhanced_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
