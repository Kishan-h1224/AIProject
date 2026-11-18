
import sqlite3
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, Request

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.schemas import (
    AgentRequest,
    AgentResponse,
    UserCreateRequest,
    ApprovalDecisionRequest
)

from app.api.security import (
    get_current_user,
    require_admin
)

from app.api.user_store import (
    initialize_database,
    create_user,
    get_all_users,
    deactivate_user
)

from app.api.roles import get_permissions

from app.api.approval_store import (
    initialize_approval_db,
    create_approval,
    get_pending_approval,
    claim_approval,
    reject_approval
)

from app.memory.conversation_store import (
    initialize_conversation_db,
    save_message,
    get_conversation
)

from app.agent.controller import AutoAgent
from app.agent.mock_llm import MockLLM

from app.tools.registry import (
    list_tools,
    get_tool
)

# Import every tool module so its decorator registers the tool.
from app.tools import (
    basic_tools,
    web_search,
    python_executor,
    sql_tool,
    file_tool
)


# ---------------------------------
# 1. Initialize databases
# ---------------------------------

initialize_database()
initialize_conversation_db()
initialize_approval_db()


# ---------------------------------
# 2. FastAPI configuration
# ---------------------------------

limiter = Limiter(
    key_func=get_remote_address
)

app = FastAPI(
    title="AutoAgent API",
    description="REST API for the autonomous AI agent",
    version="1.0.0"
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# ---------------------------------
# 3. Initialize agent
# ---------------------------------

agent = AutoAgent(
    llm=MockLLM(),
    allowed_tools=set(list_tools()),
    max_steps=5,
    max_retries=2,
    max_identical_calls=2
)


# ---------------------------------
# 4. Admin endpoints
# ---------------------------------

@app.post("/admin/users")
def admin_create_user(
    payload: UserCreateRequest,
    role: str = Depends(require_admin)
):
    try:
        api_key = create_user(
            username=payload.username,
            role=payload.role
        )

        return {
            "success": True,
            "username": payload.username,
            "role": payload.role,
            "api_key": api_key
        }

    except (sqlite3.IntegrityError, ValueError):
        raise HTTPException(
            status_code=409,
            detail="Username already exists or is invalid"
        )


@app.get("/admin/users")
def admin_get_users(
    role: str = Depends(require_admin)
):
    return {
        "users": get_all_users()
    }


@app.patch("/admin/users/{username}/deactivate")
def admin_deactivate_user(
    username: str,
    role: str = Depends(require_admin)
):
    success = deactivate_user(username)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "message": f"User {username} deactivated"
    }


# ---------------------------------
# 5. Basic endpoints
# ---------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to AutoAgent API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ---------------------------------
# 6. Run agent
# ---------------------------------

@app.post("/agent/run", response_model=AgentResponse)
@limiter.limit("10/minute")
def run_agent(
    request: Request,
    payload: AgentRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    role = current_user["role"]

    conversation_id = (
        payload.conversation_id or str(uuid4())
    )

    # Retrieve previous conversation.
    history = get_conversation(
        user_id,
        conversation_id
    )

    # Save current user message.
    save_message(
        user_id,
        conversation_id,
        "user",
        payload.message
    )

    # Run the agent with role-based permissions.
    result = agent.run(
        payload.message,
        allowed_tools=get_permissions(role),
        conversation_history=history
    )

    # Handle a pending approval request.
    if result["status"] == "approval_required":

        pending = result["pending_approval"]

        # Store the exact tool operation on the server.
        approval_id = create_approval(
            user_id=user_id,
            conversation_id=conversation_id,
            tool_name=pending["tool_name"],
            arguments=pending["arguments"]
        )

        approval_details = {
            "approval_id": approval_id,
            "tool_name": pending["tool_name"],
            "arguments": pending["arguments"],
            "status": "pending"
        }

        return AgentResponse(
            success=True,
            result=result,
            error=None,
            conversation_id=conversation_id,
            pending_approval=approval_details
        )

    # Save successful answer.
    if result["status"] == "completed":

        save_message(
            user_id,
            conversation_id,
            "assistant",
            str(result["answer"])
        )

        return AgentResponse(
            success=True,
            result=result,
            error=None,
            conversation_id=conversation_id
        )

    return AgentResponse(
        success=False,
        result=result,
        error=result["error"],
        conversation_id=conversation_id
    )


# ---------------------------------
# 7. Approve or reject operation
# ---------------------------------

@app.post("/approvals/{approval_id}")
@limiter.limit("10/minute")
def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    role = current_user["role"]

    # Retrieve only this user's pending approval.
    pending = get_pending_approval(
        approval_id,
        user_id
    )

    if pending is None:
        raise HTTPException(
            status_code=404,
            detail="Pending approval not found"
        )

    # Handle rejection.
    if not payload.approved:

        rejected = reject_approval(
            approval_id,
            user_id
        )

        if not rejected:
            raise HTTPException(
                status_code=409,
                detail="Approval is no longer pending"
            )

        save_message(
            user_id,
            pending["conversation_id"],
            "assistant",
            f"Operation {approval_id} was rejected."
        )

        return {
            "success": True,
            "status": "rejected",
            "message": "Operation was rejected."
        }

    # Check current role permissions.
    if pending["tool_name"] not in get_permissions(role):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to execute this tool"
        )

    # Retrieve the registered tool.
    try:
        tool = get_tool(pending["tool_name"])

        # Validate the stored arguments again.
        validated_args = tool.args_model.model_validate(
            pending["arguments"]
        )

        arguments = validated_args.model_dump()

        # Verify that this operation actually requires approval.
        if not tool.needs_approval(arguments):
            raise HTTPException(
                status_code=400,
                detail="This operation does not require approval"
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Stored approval operation is invalid"
        )

    # Atomically claim approval before executing.
    claimed = claim_approval(
        approval_id,
        user_id
    )

    if claimed is None:
        raise HTTPException(
            status_code=409,
            detail="Approval has already been used or is no longer pending"
        )

    # Execute the exact stored operation once.
    try:
        execution_result = tool.func(**arguments)

    except Exception as exc:
        save_message(
            user_id,
            pending["conversation_id"],
            "assistant",
            f"Approved operation failed: {str(exc)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Approved operation failed: {str(exc)}"
        )

    # Save execution result in conversation history.
    save_message(
        user_id,
        pending["conversation_id"],
        "assistant",
        str(execution_result)
    )

    return {
        "success": True,
        "status": "executed",
        "tool_name": pending["tool_name"],
        "result": execution_result
    }
