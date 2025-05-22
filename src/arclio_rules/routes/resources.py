from fastmcp import FastMCP


# Static resource
@mcp.resource("config://version")
def get_version():
    """Get the version of the application.

    Returns:
        string: The version of the application.
    """
    return "2.0.1"


# Dynamic resource template
@mcp.resource("users://{user_id}/profile")
def get_inhouse_rules(rule_id: int):
    """Get in-house rules for a specific user.

    Args:
        rule_id (int): The ID of the rule to be fetched.

    Returns:
        dict: A dictionary containing the rule name, content, and status.
    """
    rule = get_inhouse_rule(rule_id=rule_id)
    return {
        "name": f"Rule:{rule_id}",
        "content": rule,
        "status": "active",
    }


def get_inhouse_rule(rule_id: int) -> str:
    """Fetch the content of an in-house rule.

    Args:
        rule_id (int): The ID of the rule to be fetched.

    Returns:
        str: The content of the rule.
    """
    # open the file in read mode
    with open(f"../inhouse_rules/rule_{rule_id}.md", "r") as file:
        rule = file.read()
    return rule
