# import re
# import time
# from typing import Any, Dict, List, Optional

# import frontmatter
# from pydantic import BaseModel

# from arclio_rules.services.rule_fetch_service import RuleFetchService

# rule_fetch_service = RuleFetchService(config={})


# class RuleCacheEntry(BaseModel):
#     data: Dict[str, Any]
#     expiry: float


# class RuleReference(BaseModel):
#     path: str
#     section: Optional[str] = None


# class ResolvedRule(BaseModel):
#     rule: Dict[str, Any]
#     dependencies: List[Dict[str, Any]]


# class RuleResolutionService:
#     def __init__(self, config):
#         """Initialize the RuleResolutionService.

#         Args:
#             config (dict): Configuration dictionary containing necessary parameters.
#         """
#         self.rule_cache = {}  # Dict[str, RuleCacheEntry]
#         self.CACHE_TTL = 5 * 60  # 5 minutes in seconds
#         self.config = config

#     async def get_rule(self, client_id: str, rule_path: str) -> Dict[str, Any]:
#         """Get a rule with caching."""
#         cache_key = f"{client_id}:{rule_path}"

#         # Check cache first
#         if cache_key in self.rule_cache:
#             cache_entry = self.rule_cache[cache_key]
#             if cache_entry.expiry > time.time():
#                 return cache_entry.data
#             # Expired, remove from cache
#             del self.rule_cache[cache_key]

#         # Fetch from storage
#         result = await rule_fetch_service.get_rule_content(client_id, rule_path)

#         if not result["success"]:
#             raise Exception(f"Failed to retrieve rule: {rule_path}")

#         content = result["content"]
#         post = frontmatter.loads(content)

#         rule = {"path": rule_path, "content": post.content, "metadata": post.metadata}

#         # Store in cache
#         self.rule_cache[cache_key] = RuleCacheEntry(
#             data=rule, expiry=time.time() + self.CACHE_TTL
#         )

#         return rule

#     def extract_rule_references(self, content: str) -> List[RuleReference]:
#         """Extract references to other rules."""
#         references = []
#         pattern = r"@([a-zA-Z0-9_\-\/]+\.mdc)(?:#([a-zA-Z0-9_\-]+))?"

#         for match in re.finditer(pattern, content):
#             references.append(
#                 RuleReference(path=match.group(1), section=match.group(2))
#             )

#         return references

#     async def resolve_rule_with_dependencies(
#         self, client_id: str, rule_path: str
#     ) -> ResolvedRule:
#         """Resolve a rule and all its dependencies."""
#         rule = await self.get_rule(client_id, rule_path)
#         dependencies = []

#         # Process explicit dependencies from metadata
#         if "dependencies" in rule["metadata"]:
#             for dep_path in rule["metadata"]["dependencies"]:
#                 # Remove @ prefix if present
#                 clean_path = dep_path[1:] if dep_path.startswith("@") else dep_path
#                 dep_rule = await self.get_rule(client_id, clean_path)
#                 dependencies.append(dep_rule)

#         # Process implicit dependencies from content
#         references = self.extract_rule_references(rule["content"])
#         for ref in references:
#             if not any(d["path"] == ref.path for d in dependencies):
#                 dep_rule = await self.get_rule(client_id, ref.path)
#                 dependencies.append(dep_rule)

#         return ResolvedRule(rule=rule, dependencies=dependencies)

#     async def apply_rules_to_context(
#         self, client_id: str, rule_paths: List[str], current_context: str = ""
#     ) -> str:
#         """Apply rules to provide context for AI."""
#         enhanced_context = current_context

#         for path in rule_paths:
#             try:
#                 resolved = await self.resolve_rule_with_dependencies(client_id, path)

#                 # Add rule content to context
#                 enhanced_context += (
#                     f"\n\n### Rule: {resolved.rule['path']}\n{resolved.rule['content']}" # noqa: E501
#                 )

#                 # Add dependencies to context
#                 for dep in resolved.dependencies:
#                     enhanced_context += (
#                         f"\n\n### Dependency: {dep['path']}\n{dep['content']}"
#                     )
#             except Exception as e:
#                 # Log the error but continue with other rules
#                 print(f"Error applying rule {path}: {str(e)}")

#         return enhanced_context
