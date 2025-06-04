from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from arclio_rules.services.rule_indexing_service import RuleIndexingService
from arclio_rules.services.rule_resolution_service import RuleResolutionService
from arclio_rules.services.rule_storage_service import (
    RuleStorageService,
)

router = APIRouter(prefix="/api/rules")
rule_storage_service = RuleStorageService(config={})
rule_indexing_service = RuleIndexingService(config={})
rule_resolution_service = RuleResolutionService(config={})


class ApplyRulesRequest(BaseModel):
    rule_paths: List[str]
    current_context: str


# Load the main rule
@router.post("/load_main_rule", operation_id="load_main_rule")
async def load_main_rule():
    """Load the main rule from the client repository.

    Returns:
        dict: A dictionary containing the success status and the rule content.
    """
    result = await rule_storage_service.get_rule_content(
        client_name="", rule_path="index.mdc"
    )
    if result["success"]:
        return {"success": True, "content": result["content"]}
    else:
        logger.error(f"Failed to get rule: {result.get('error')}")
        raise HTTPException(status_code=404, detail="Rule not found")


@router.post("/{client_name}/{rule_path:path}", operation_id="load_rule")
async def load_rule(client_name: str, rule_path: str):
    """Load a rule from the client repository.

    Args:
        client_name (str): The name of the client whose rule is being fetched.
        rule_path (str): The path to the rule in the client's repository.

    Returns:
        dict: A dictionary containing the success status and the rule content.
    """
    result = await rule_storage_service.get_rule_content(client_name, rule_path)

    if result["success"]:
        return {"success": True, "content": result["content"]}
    else:
        logger.error(f"Failed to get rule: {result.get('error')}")
        raise HTTPException(status_code=404, detail="Rule not found")


# List rules in a directory
@router.post("/{client_name}/{directory:path}", operation_id="list_rules")
async def list_rules(directory: str = ""):
    """List rules in a directory.

    Args:
        directory (str): The directory to list rules from.

    Returns:
        dict: A dictionary containing the success status and the rules.
    """
    result = await rule_storage_service.list_rules(directory)

    if result["success"]:
        return {"success": True, "rules": result["rules"]}
    else:
        raise HTTPException(status_code=500, detail="Failed to list rules")


# # Save a rule
# @router.post("/{client_id}/{rule_path:path}", operation_id="save_rule")
# async def save_rule(client_id: str, rule_path: str, request: RuleSaveRequest):
#     """Save a rule to the client repository.

#     Args:
#         client_id (str): The ID of the client whose rule is being saved.
#         rule_path (str): The path to save the rule in the client's repository.
#         request (RuleSaveRequest): The request object containing the rule content

#     Returns:
#         dict: A dictionary containing the success status.
#     """
#     if not request.content:
#         raise HTTPException(status_code=400, detail="Content is required")

#     result = await rule_storage_service.save_rule_content(
#         client_id, rule_path, request.content, request.commit_message
#     )

#     if result["success"]:
#         # Index the rule after saving
#         await rule_indexing_service.index_rule(client_id, rule_path)
#         return {"success": True}
#     else:
#         raise HTTPException(status_code=500, detail="Failed to save rule")


# # Search rules
# @router.post("/{client_id}/search", operation_id="search_rules")
# async def search_rules(
#     client_id: str,
#     q: str = Query(..., description="Search query"),
#     limit: int = Query(10, ge=1, le=100),
# ):
#     """Search rules.

#     Args:
#         client_id (str): The ID of the client whose rules are being searched.
#         q (str): The search query.
#         limit (int): The maximum number of results to return.

#     Returns:
#         dict: A dictionary containing the success status and the search results.
#     """
#     if not q:
#         raise HTTPException(status_code=400, detail="Query is required")

#     result = await rule_indexing_service.search_rules(client_id, q, limit)

#     if result["success"]:
#         return {"success": True, "results": result["results"]}
#     else:
#         raise HTTPException(status_code=500, detail="Search failed")


# # Apply rules to context
# @router.post("/{client_id}/apply", operation_id="apply_rules")
# async def apply_rules(client_id: str, request: ApplyRulesRequest):
#     """Apply rules to context.

#     Args:
#         client_id (str): The ID of the client whose rules are being applied.
#         request (ApplyRulesRequest): The request object containing the rule paths and current context. # noqa: E501

#     Returns:
#         dict: A dictionary containing the success status and the enhanced context.
#     """  # noqa: E501
#     if not request.rule_paths:
#         raise HTTPException(status_code=400, detail="Rule paths array is required")

#     try:
#         enhanced_context = await rule_resolution_service.apply_rules_to_context(
#             client_id, request.rule_paths, request.current_context
#         )

#         return {"success": True, "context": enhanced_context}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
