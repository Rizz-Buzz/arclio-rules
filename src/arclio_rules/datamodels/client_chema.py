from datetime import datetime
from typing import Any, Dict, List

client_schema: Dict[str, Any] = {
    "id": str,  # Unique client identifier
    "name": str,  # Client name
    "repo_name": str,  # Name of client's rule repository
    "repo_url": str,  # URL to client's rule repository
    "enabled": bool,  # Whether this client is active
    "created_at": datetime,  # Or date
    "administrators": List[str],  # User IDs who can manage rules
    "settings": {
        "default_rules": List[str],  # Default rules to apply in conversations
        "suggestion_enabled": bool,  # Whether rule suggestions are enabled
        "auto_apply_rules": bool,  # Whether to automatically apply suggested rules
    },
}
