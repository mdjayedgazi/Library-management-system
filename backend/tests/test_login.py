"""Tests for login and authorization endpoints."""

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import settings


class TestLogin:
    """Tests for POST /auth/login."""

    def _register_user(self, client: AsyncClient, email=None, password=None):
        """Register a user and return the response."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": email or "loginuser@example.com",
            "password": password or "SecurePass123!",
        }
        return client.post("/auth/register", json=payload)

    @pytest.mark.asyncio
    async def test_successful_login_with_email(self, client: AsyncClient):
        """Test that login with valid email and password returns a token."""
        await self._register_user(client)
        response = await client.post(
            "/auth/login",
            data={
                "username": "loginuser@example.com",  # OAuth2 form uses 'username' field
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_uppercase_email(self, client: AsyncClient):
        """Test that login works with uppercase email (normalized)."""
        await self._register_user(client, email="CaseTest@Example.com")
        response = await client.post(
            "/auth/login",
            data={
                "username": "CASETEST@EXAMPLE.COM",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, client: AsyncClient):
        """Test that incorrect password returns 401."""
        await self._register_user(client)
        response = await client.post(
            "/auth/login",
            data={
                "username": "loginuser@example.com",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401
        assert "email" in response.json()["detail"].lower() or "password" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_unregistered_email(self, client: AsyncClient):
        """Test that unregistered email returns 401."""
        response = await client.post(
            "/auth/login",
            data={
                "username": "unregistered@example.com",
                "password": "SomePassword123!",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient):
        """Test that missing password returns 422."""
        response = await client.post(
            "/auth/login",
            data={"username": "loginuser@example.com"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_email(self, client: AsyncClient):
        """Test that missing email (username field) returns 422."""
        response = await client.post(
            "/auth/login",
            data={"password": "SomePassword123!"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_returns_valid_jwt_token(self, client: AsyncClient):
        """Test that the returned token is a valid JWT."""
        await self._register_user(client)
        response = await client.post(
            "/auth/login",
            data={
                "username": "loginuser@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode and verify token structure
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        assert decoded["sub"] == "loginuser@example.com"
        assert "id" in decoded
        assert decoded["role"] == "member"
        assert "exp" in decoded

    @pytest.mark.asyncio
    async def test_login_token_contains_user_id(self, client: AsyncClient):
        """Test that JWT token contains user ID."""
        await self._register_user(client)
        response = await client.post(
            "/auth/login",
            data={
                "username": "loginuser@example.com",
                "password": "SecurePass123!",
            },
        )
        token = response.json()["access_token"]
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        assert "id" in decoded
        assert isinstance(decoded["id"], int)


class TestAuthorization:
    """Tests for protected endpoints and token-based authorization."""

    async def _register_and_login(self, client: AsyncClient, email=None, password=None):
        """Register and login, return the access token."""
        email = email or "authuser@example.com"
        password = password or "AuthPass123!"
        await client.post("/auth/register", json={
            "first_name": "Auth",
            "last_name": "User",
            "email": email,
            "password": password,
        })
        response = await client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, client: AsyncClient):
        """Test that protected endpoints return 401 without token."""
        response = await client.get("/books/reservation/my")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_authenticates_successfully(self, client: AsyncClient):
        """Test that a valid token authenticates successfully."""
        token = await self._register_and_login(client)
        response = await client.get(
            "/books/reservation/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client: AsyncClient):
        """Test that an invalid token is rejected."""
        response = await client.get(
            "/books/reservation/my",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_edit_user_with_valid_token(self, client: AsyncClient):
        """Test that editing user profile works with valid token."""
        token = await self._register_and_login(client)
        response = await client.patch(
            "/auth/edituser",
            json={"first_name": "Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_change_password_with_valid_token(self, client: AsyncClient):
        """Test that changing password works with valid token."""
        email = "changepass@example.com"
        old_password = "OldPass123!"
        new_password = "NewPass123!"

        await client.post("/auth/register", json={
            "first_name": "Change",
            "last_name": "Pass",
            "email": email,
            "password": old_password,
        })

        login_resp = await client.post(
            "/auth/login",
            data={"username": email, "password": old_password},
        )
        token = login_resp.json()["access_token"]

        response = await client.patch(
            "/auth/changepassword",
            json={
                "current_password": old_password,
                "new_password": new_password,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify old password no longer works
        login_response = await client.post(
            "/auth/login",
            data={"username": email, "password": old_password},
        )
        assert login_response.status_code == 401

        # Verify new password works
        login_response = await client.post(
            "/auth/login",
            data={"username": email, "password": new_password},
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_librarian_role(self, client: AsyncClient):
        """Test that admin endpoints require librarian role."""
        token = await self._register_and_login(client)
        response = await client.post(
            "/admin/add_book",
            data={
                "title": "Test Book",
                "author": "Test Author",
                "description": "Test Description",
                "price": "10.0",
                "total_copies": "5",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # Member role should not be able to access admin endpoints
        assert response.status_code == 401
