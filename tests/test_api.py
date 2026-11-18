
from fastapi.testclient import TestClient
import pytest

from app.api.main import app, agent
import uuid
from app.api.user_store import create_user

client = TestClient(app)


# Set test API key automatically before each test
@pytest.fixture(autouse=True)
def set_test_api_keys():

    suffix = uuid.uuid4().hex[:10]

    return {
        "admin": create_user(f"test_admin_{suffix}", "admin"),
        "developer": create_user(f"test_developer_{suffix}", "developer"),
        "analyst": create_user(f"test_analyst_{suffix}", "analyst"),
        "guest": create_user(f"test_guest_{suffix}", "guest")
    }


def test_home_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Welcome to AutoAgent API",
        "status": "running"
    }


def test_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


def test_agent_execution(monkeypatch, set_test_api_keys):

    def mock_run(message, allowed_tools=None, conversation_history=None):

        assert message == "Calculate 25 multiplied by 4"

        return {
            "status": "completed",
            "answer": "The final answer is 100",
            "error": None,
            "tool_calls": 1,
            "execution_attempts": 1,
            "observations": [],
            "state_history": ["THINK", "DONE"]
        }

    monkeypatch.setattr(agent, "run", mock_run)

    response = client.post(
        "/agent/run",
        json={
            "message": "Calculate 25 multiplied by 4"
        },
        headers={
            "X-API-Key": set_test_api_keys["admin"]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["result"]["answer"] == "The final answer is 100"


def test_empty_message(set_test_api_keys):

    response = client.post(
        "/agent/run",
        json={},
        headers={
            "X-API-Key": set_test_api_keys["admin"]
        }
    )

    assert response.status_code == 422


def test_empty_message(set_test_api_keys):

    response = client.post(
        "/agent/run",
        json={
            "message": ""
        },
        headers={
            "X-API-Key": set_test_api_keys["admin"]
        }
    )

    assert response.status_code == 422


def test_missing_api_key():

    response = client.post(
        "/agent/run",
        json={
            "message": "Calculate 25 multiplied by 4"
        }
    )

    assert response.status_code == 401


def test_invalid_api_key():

    response = client.post(
        "/agent/run",
        json={
            "message": "Calculate 25 multiplied by 4"
        },
        headers={
            "X-API-Key": "wrong-key"
        }
    )

    assert response.status_code == 401
