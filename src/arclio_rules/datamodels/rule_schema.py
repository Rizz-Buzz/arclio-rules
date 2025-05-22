from datetime import date, datetime
from typing import Any, Dict, List

rule_schema: Dict[str, Any] = {
    "path": str,  # Full path to the rule within the repository
    "displayPath": str,  # Formatted path for display (@path/to/rule.mdc)
    "content": str,  # Raw file content including frontmatter
    "metadata": {
        "description": str,
        "version": str,
        "owner": str,
        "last_updated": date,  # Or datetime, depending on precision needed
        "applies_to": List[str],
        "dependencies": List[str],
    },
    "parsed_content": str,  # Markdown content without frontmatter
    "html_content": str,  # HTML rendered version of the markdown
    "client_id": str,  # ID of the client who owns this rule
    "created_at": datetime,  # Or date
    "updated_at": datetime,  # Or date
    "created_by": str,
    "updated_by": str,
}
