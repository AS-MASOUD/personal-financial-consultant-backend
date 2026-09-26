import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


async def get_auth_token(client: AsyncClient, email: str = "sysmanager@personal-fc.local") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "AdminPassword123!"},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_roles_definition():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/users/roles")
        assert res.status_code == 200
        roles = res.json()
        assert len(roles) == 4
        role_names = [r["role"] for r in roles]
        assert "sysmanager" in role_names
        assert "admin" in role_names
        assert "user" in role_names
        assert "viewer" in role_names


@pytest.mark.asyncio
async def test_users_crud_and_safeguards():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sys_token = await get_auth_token(client, "sysmanager@personal-fc.local")
        sys_headers = {"Authorization": f"Bearer {sys_token}"}

        # 1. List users
        res_list = await client.get("/api/v1/users", headers=sys_headers)
        assert res_list.status_code == 200
        data = res_list.json()
        assert data["total"] >= 4
        assert len(data["items"]) >= 4

        # 2. Regular user cannot access /api/v1/users
        user_token = await get_auth_token(client, "user@personal-fc.local")
        user_headers = {"Authorization": f"Bearer {user_token}"}
        res_denied = await client.get("/api/v1/users", headers=user_headers)
        assert res_denied.status_code == 403

        # 3. Create a new user with 'admin' role
        import uuid

        unique_officer_email = f"finance.officer.{uuid.uuid4().hex[:8]}@personal-fc.local"
        create_payload = {
            "email": unique_officer_email,
            "password": "TempPassword123!",
            "full_name": "Finance Officer",
            "role": "admin",
            "is_active": True,
        }
        res_create = await client.post("/api/v1/users", headers=sys_headers, json=create_payload)
        assert res_create.status_code == 201
        created_user = res_create.json()
        user_id = created_user["id"]
        assert created_user["role"] == "admin"

        # 4. Promote user to sysmanager
        res_role = await client.patch(
            f"/api/v1/users/{user_id}/role",
            headers=sys_headers,
            json={"role": "sysmanager"},
        )
        assert res_role.status_code == 200
        assert res_role.json()["role"] == "sysmanager"

        # 5. Deactivate user
        res_deact = await client.patch(
            f"/api/v1/users/{user_id}/status",
            headers=sys_headers,
            json={"is_active": False},
        )
        assert res_deact.status_code == 200
        assert res_deact.json()["is_active"] is False

        # 6. Reactivate user
        res_react = await client.patch(
            f"/api/v1/users/{user_id}/status",
            headers=sys_headers,
            json={"is_active": True},
        )
        assert res_react.status_code == 200
        assert res_react.json()["is_active"] is True

        # 7. Delete user
        res_del = await client.delete(f"/api/v1/users/{user_id}", headers=sys_headers)
        assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_last_sysmanager_safeguard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sys_token = await get_auth_token(client, "sysmanager@personal-fc.local")
        sys_headers = {"Authorization": f"Bearer {sys_token}"}

        # Fetch current sysmanager
        me_res = await client.get("/api/v1/auth/me", headers=sys_headers)
        sys_id = me_res.json()["id"]

        # Attempt to demote self (the only sysmanager) -> must fail
        demote_res = await client.patch(
            f"/api/v1/users/{sys_id}/role",
            headers=sys_headers,
            json={"role": "user"},
        )
        assert demote_res.status_code == 400

        # Attempt to deactivate self -> must fail
        deact_res = await client.patch(
            f"/api/v1/users/{sys_id}/status",
            headers=sys_headers,
            json={"is_active": False},
        )
        assert deact_res.status_code == 400

        # Attempt to delete self -> must fail
        del_res = await client.delete(f"/api/v1/users/{sys_id}", headers=sys_headers)
        assert del_res.status_code == 400
