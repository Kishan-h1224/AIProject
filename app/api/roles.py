
ROLE_PERMISSIONS = {

    "admin": {
        "add",
        "subtract",
        "multiply",
        "web_search",
        "python_executor",
        "sql_executor",
        "file_io"
    },

    "developer": {
        "add",
        "subtract",
        "multiply",
        "web_search",
        "python_executor",
        "file_io"
    },

    "analyst": {
        "add",
        "subtract",
        "multiply",
        "web_search",
        "sql_executor"
    },

    "guest": {
        "add",
        "subtract",
        "multiply"
    }
}


def get_permissions(role: str) -> set[str]:

    if role not in ROLE_PERMISSIONS:
        raise ValueError("Invalid user role")

    return ROLE_PERMISSIONS[role]


def has_permission(role: str, tool_name: str) -> bool:

    permissions = get_permissions(role)

    return tool_name in permissions
