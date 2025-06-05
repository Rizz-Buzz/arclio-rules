from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from arclio_rules.services.rule_fetch_service import (
    RuleFetchService,
)

# from arclio_rules.services.rule_indexing_service import RuleIndexingService
# from arclio_rules.services.rule_resolution_service import RuleResolutionService

router = APIRouter(prefix="/api/rules")
rule_fetch_service = RuleFetchService(config={})
# rule_indexing_service = RuleIndexingService(config={})
# rule_resolution_service = RuleResolutionService(config={})


class ApplyRulesRequest(BaseModel):
    rule_paths: List[str]
    current_context: str


class RuleSaveRequest(BaseModel):
    content: str
    commit_message: str = "Update rule content"


@router.post("/rules", operation_id="list_companies")
async def list_companies():
    """List all companies.

    Returns:
        dict: A dictionary containing a list of all companies.
    """
    result = rule_fetch_service.list_all_companies()
    return {"companies": result}


@router.post("/rules/{company}", operation_id="get_company_categories")
async def get_company_categories(company: str):
    """List categories for a company.

    Args:
        company (str): The name of the company whose categories are being listed.

    Returns:
        dict: A dictionary containing the company name and a list of categories.
    """
    result = rule_fetch_service.list_company_categories(company)
    return {
        "company": company,
        "categories": result,
    }


@router.post("/rules/{company}/{category}", operation_id="get_category_rules")
async def get_category_rules(company: str, category: str):
    """List rules in a category.

    Args:
        company (str): The name of the company whose category rules are being listed.
        category (str): The name of the category whose rules are being listed.

    Returns:
        dict: A dictionary containing the company name, category name, and a list of rules in that category.
    """  # noqa: E501
    result = rule_fetch_service.list_category_rules(company, category)
    return {
        "company": company,
        "category": category,
        "rules": result,
    }


@router.post("/rules/{company}/{category}/{rule}", operation_id="get_rule")
async def get_rule(company: str, category: str, rule: str):
    """Fetch a specific rule.

    Args:
        company (str): The name of the company whose rule is being fetched.
        category (str): The category of the rule.
        rule (str): The name of the rule.

    Returns:
        dict: A dictionary containing the rule content.
    """
    return rule_fetch_service.get_rule(company, category, rule)


@router.post("/main_rule", operation_id="get_main_rule")
async def get_main_rule():
    """Fetch the main rule.

    Returns:
        dict: A dictionary containing the rule content.
    """
    return rule_fetch_service.get_rule(
        company="", category="", rule="", is_main_rule=True
    )


# Save a rule
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

#     result = await rule_fetch_service.save_rule_content(
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
