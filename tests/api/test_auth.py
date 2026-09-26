import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_auth_login_and_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login with seeded sysmanager
        login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "sysmanager@personal-fc.local",
                "password": "AdminPassword123!",
            },
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["user"]["role"] == "sysmanager"
        assert token_data["user"]["email"] == "sysmanager@personal-fc.local"

        token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. Get me with bearer token
        me_res = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["email"] == "sysmanager@personal-fc.local"
        assert me_data["role"] == "sysmanager"

        # 3. Refresh token
        refresh_res = await client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert refresh_res.status_code == 200
        new_token_data = refresh_res.json()
        assert "access_token" in new_token_data

        # 4. Unauthenticated access fails
        fail_res = await client.get("/api/v1/auth/me")
        assert fail_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Wrong password
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "sysmanager@personal-fc.local",
                "password": "WrongPassword!",
            },
        )
        assert res.status_code == 401

        # Nonexistent user
        res_nonexistent = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@personal-fc.local",
                "password": "AnyPassword123!",
            },
        )
        assert res_nonexistent.status_code == 404
        assert res_nonexistent.json()["error"]["code"] == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_auth_register_and_change_password():
    import uuid

    unique_email = f"new.member.{uuid.uuid4().hex[:8]}@personal-fc.local"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register new user
        reg_payload = {
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "New Team Member",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == unique_email
        assert data["user"]["role"] == "user"  # Because seed users already exist
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Duplicate register fails
        dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert dup_res.status_code == 409

        # Change password
        cp_payload = {
            "old_password": "SecurePassword123!",
            "new_password": "NewSecurePassword456!",
        }
        cp_res = await client.post("/api/v1/auth/change-password", headers=headers, json=cp_payload)
        assert cp_res.status_code == 200

        # Login with new password
        login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "NewSecurePassword456!",
            },
        )
        assert login_res.status_code == 200

        # Update profile (age, job, bio, full_name)
        update_profile_res = await client.patch(
            "/api/v1/auth/me",
            headers=headers,
            json={
                "full_name": "نام ویرایش شده",
                "age": 32,
                "job": "تحلیل‌گر بازارهای مالی",
                "bio": "علاقه‌مند به اقتصاد کلان و سرمایه‌گذاری",
            },
        )
        assert update_profile_res.status_code == 200
        profile_data = update_profile_res.json()
        assert profile_data["full_name"] == "نام ویرایش شده"
        assert profile_data["age"] == 32
        assert profile_data["job"] == "تحلیل‌گر بازارهای مالی"
        assert profile_data["bio"] == "علاقه‌مند به اقتصاد کلان و سرمایه‌گذاری"

