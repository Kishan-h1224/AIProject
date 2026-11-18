
import pytest
import uuid

from fastapi.testclient import TestClient

from app.api.main import app, agent
from app.api.user_store import create_user


client = TestClient(app)


@pytest.fixture(autouse=True)
def set_test_api_keys():

    suffix = uuid.uuid4().hex[:10]

    return {
        "admin": create_user(f"test_admin_{suffix}", "admin"),
        "developer": create_user(f"test_developer_{suffix}", "developer"),
        "analyst": create_user(f"test_analyst_{suffix}", "analyst"),
        "guest": create_user(f"test_guest_{suffix}", "guest")
    }


def test_guest_role_permissions(monkeypatch, set_test_api_keys):

    def mock_run(message, allowed_tools=None, conversation_history=None):

        assert allowed_tools == {
            "add",
            "subtract",
            "multiply"
        }

        return {
            "status": "completed",
            "answer": "100",
            "error": None,
            "tool_calls": 1,
            "execution_attempts": 1,
            "observations": [],
            "state_history": ["THINK", "DONE"]
        }

    monkeypatch.setattr(agent, "run", mock_run)

    response = client.post(
        "/agent/run",
        json={"message": "Calculate 25 multiplied by 4"},
        headers={"X-API-Key": set_test_api_keys["guest"]}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_analyst_role_permissions(monkeypatch, set_test_api_keys):

    def mock_run(message, allowed_tools=None, conversation_history=None):

        assert "sql_executor" in allowed_tools
        assert "python_executor" not in allowed_tools

        return {
            "status": "completed",
            "answer": "Analyst access verified",
            "error": None,
            "tool_calls": 0,
            "execution_attempts": 0,
            "observations": [],
            "state_history": ["THINK", "DONE"]
        }

    monkeypatch.setattr(agent, "run", mock_run)

    response = client.post(
        "/agent/run",
        json={"message": "Test analyst access"},
        headers={"X-API-Key": set_test_api_keys["analyst"]}
    )

    assert response.status_code == 200


def test_developer_role_permissions(monkeypatch, set_test_api_keys):

    def mock_run(message, allowed_tools=None, conversation_history=None):

        assert "python_executor" in allowed_tools
        assert "sql_executor" not in allowed_tools

        return {
            "status": "completed",
            "answer": "Developer access verified",
            "error": None,
            "tool_calls": 0,
            "execution_attempts": 0,
            "observations": [],
            "state_history": ["THINK", "DONE"]
        }

    monkeypatch.setattr(agent, "run", mock_run)

    response = client.post(
        "/agent/run",
        json={"message": "Test developer access"},
        headers={"X-API-Key": set_test_api_keys["developer"]}
    )

    assert response.status_code == 200


def test_admin_role_permissions(monkeypatch, set_test_api_keys):

    def mock_run(message, allowed_tools=None, conversation_history=None):

        assert len(allowed_tools) == 7

        return {
            "status": "completed",
            "answer": "Admin access verified",
            "error": None,
            "tool_calls": 0,
            "execution_attempts": 0,
            "observations": [],
            "state_history": ["THINK", "DONE"]
        }

    monkeypatch.setattr(agent, "run", mock_run)

    response = client.post(
        "/agent/run",
        json={"message": "Test admin access"},
        headers={"X-API-Key": set_test_api_keys["admin"]}
    )

    assert response.status_code == 200
