from fastapi import APIRouter, Depends

from arclio_rules.services.rule_indexing_service import RuleIndexingService
from arclio_rules.services.rule_saving_service import RuleSavingService

router = APIRouter(prefix="/api/rules")


def get_indexer():
    """Dependency to get the RuleIndexingService instance."""
    return RuleIndexingService(max_cache_size=1000, ttl_seconds=3600)


def get_saver():
    """Dependency to get the RuleSavingService instance."""
    return RuleSavingService()


@router.post("/rules", operation_id="list_companies")
async def list_companies(indexer: RuleIndexingService = Depends(get_indexer)):
    """List all companies.

    Args:
        indexer (RuleIndexingService): The indexing service to fetch the companies.

    Returns:
        dict: A dictionary containing a list of all companies.
    """
    result = indexer.list_all_companies()
    return {"companies": result}


@router.post("/rules/{company}", operation_id="get_company_categories")
async def get_company_categories(
    company: str, indexer: RuleIndexingService = Depends(get_indexer)
):
    """List categories for a company.

    Args:
        company (str): The name of the company whose categories are being listed.
        indexer (RuleIndexingService): The indexing service to fetch the categories.

    Returns:
        dict: A dictionary containing the company name and a list of categories.
    """
    result = indexer.list_company_categories(company)
    return {
        "company": company,
        "categories": result,
    }


@router.post("/rules/{company}/{category}", operation_id="get_category_rules")
async def get_category_rules(
    company: str, category: str, indexer: RuleIndexingService = Depends(get_indexer)
):
    """List rules in a category.

    Args:
        company (str): The name of the company whose category rules are being listed.
        category (str): The name of the category whose rules are being listed.
        indexer (RuleIndexingService): The indexing service to fetch the rules.

    Returns:
        dict: A dictionary containing the company name, category name, and a list of rules in that category.
    """  # noqa: E501
    result = indexer.list_category_rules(company, category)
    return {
        "company": company,
        "category": category,
        "rules": result,
    }


@router.post("/rules/{company}/{category}/{rule}", operation_id="get_rule")
async def get_rule(
    company: str,
    category: str,
    rule: str,
    indexer: RuleIndexingService = Depends(get_indexer),
):
    """Fetch a specific rule.

    Args:
        company (str): The name of the company whose rule is being fetched.
        category (str): The category of the rule.
        rule (str): The name of the rule.
        indexer (RuleIndexingService): The indexing service to fetch the rule.

    Returns:
        dict: A dictionary containing the rule content.
    """
    return indexer.get_rule(company, category, rule)


@router.post("/main_rule", operation_id="get_main_rule")
async def get_main_rule(indexer: RuleIndexingService = Depends(get_indexer)):
    """Fetch the main rule.

    Args:
        indexer (RuleIndexingService): The indexing service to fetch the main rule.

    Returns:
        dict: A dictionary containing the rule content.
    """
    return indexer.get_rule(company="", category="", rule="", is_main_rule=True)


@router.put("/rules/{company}/{category}/{rule}", operation_id="save_rule")
async def save_rule(
    company: str,
    category: str,
    rule: str,
    content: str,
    saver: RuleSavingService = Depends(get_saver),
):
    """Save a rule to GitHub.

    Args:
        company (str): The name of the company whose rule is being saved.
        category (str): The category of the rule.
        rule (str): The name of the rule.
        content (str): The content of the rule.
        saver (RuleSavingService): The service to save the rule.

    Returns:
        dict: A dictionary containing the status and path of the saved rule.
    """
    return saver.save_rule(company, category, rule, content)
