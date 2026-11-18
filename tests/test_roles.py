
import pytest

from app.api.roles import (
    get_permissions,
    has_permission
)


def test_admin_permissions():

    permissions = get_permissions("admin")

    assert len(permissions) == 7

    assert "python_executor" in permissions
    assert "sql_executor" in permissions


def test_guest_permissions():

    permissions = get_permissions("guest")

    assert permissions == {
        "add",
        "subtract",
        "multiply"
    }


def test_developer_permissions():

    assert has_permission(
        "developer",
        "python_executor"
    )

    assert not has_permission(
        "developer",
        "sql_executor"
    )


def test_analyst_permissions():

    assert has_permission(
        "analyst",
        "sql_executor"
    )

    assert not has_permission(
        "analyst",
        "python_executor"
    )


def test_guest_cannot_execute_python():

    assert not has_permission(
        "guest",
        "python_executor"
    )


def test_invalid_role():

    with pytest.raises(ValueError):
        get_permissions("unknown")
