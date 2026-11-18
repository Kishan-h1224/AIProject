
from typing import Callable, Any
from dataclasses import dataclass
from pydantic import BaseModel


ApprovalRule = bool | Callable[[dict[str, Any]], bool]


@dataclass
class ToolDefinition:
    name: str
    func: Callable
    args_model: type[BaseModel]
    description: str
    approval_rule: ApprovalRule = False

    def needs_approval(self, arguments: dict[str, Any]) -> bool:
        if callable(self.approval_rule):
            return self.approval_rule(arguments)

        return self.approval_rule


# Central registry
TOOL_REGISTRY: dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    args_model: type[BaseModel],
    requires_approval: ApprovalRule = False
):

    def decorator(func: Callable):

        if name in TOOL_REGISTRY:
            raise ValueError(f"Tool '{name}' already registered")

        TOOL_REGISTRY[name] = ToolDefinition(
            name=name,
            func=func,
            args_model=args_model,
            description=func.__doc__ or "",
            approval_rule=requires_approval
        )

        return func

    return decorator


def get_tool(name: str) -> ToolDefinition:

    if name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' not found")

    return TOOL_REGISTRY[name]


def list_tools() -> list[str]:

    return list(TOOL_REGISTRY.keys())


def get_tool_schemas() -> list[dict]:

    schemas = []

    for tool in TOOL_REGISTRY.values():

        schemas.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args_model.model_json_schema(),
            "approval_required": (
                "conditional"
                if callable(tool.approval_rule)
                else tool.approval_rule
            )
        })

    return schemas


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    allowed_tools: set[str]
) -> Any:

    # Step 1: Check authorization
    if name not in allowed_tools:
        raise PermissionError(
            f"Tool '{name}' is not allowed"
        )

    # Step 2: Retrieve registered tool
    tool = get_tool(name)

    # Step 3: Validate arguments
    validated_args = tool.args_model.model_validate(arguments)

    # Step 4: Execute validated function
    return tool.func(**validated_args.model_dump())
