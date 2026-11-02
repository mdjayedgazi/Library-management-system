"""Tests for user registration endpoint."""

import pytest
from httpx import AsyncClient


class TestRegistration:
    """Tests for POST /auth/register."""

    def _valid_payload(self, **overrides):
        """Return a valid registration payload with optional overrides."""
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
        }
        payload.update(overrides)
        return payload

    @pytest.mark.asyncio
    async def test_successful_registration(self, client: AsyncClient):
        """Test that a valid registration returns 201 and user data."""
        response = await client.post("/auth/register", json=self._valid_payload())
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john.doe@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["role"] == "member"
        assert data["is_active"] is True
        # Password hash must never be returned
        assert "hash_password" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_registration_normalizes_email(self, client: AsyncClient):
        """Test that email is normalized to lowercase."""
        response = await client.post(
            "/auth/register", json=self._valid_payload(email="  NORMALIZE.TEST@EXAMPLE.COM  ")
        )
        assert response.status_code == 201
        assert response.json()["email"] == "normalize.test@example.com"

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, client: AsyncClient):
        """Test that registering with the same email returns 409 Conflict."""
        payload = self._valid_payload()
        await client.post("/auth/register", json=payload)
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_duplicate_email_case_insensitive(self, client: AsyncClient):
        """Test that duplicate email detection is case-insensitive."""
        await client.post(
            "/auth/register", json=self._valid_payload(email="test@example.com")
        )
        response = await client.post(
            "/auth/register",
            json=self._valid_payload(email="TEST@EXAMPLE.COM"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(self, client: AsyncClient):
        """Test that invalid email format is rejected."""
        response = await client.post(
            "/auth/register", json=self._valid_payload(email="not-an-email")
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_password_rejected(self, client: AsyncClient):
        """Test that missing password is rejected."""
        payload = self._valid_payload()
        del payload["password"]
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_first_name_rejected(self, client: AsyncClient):
        """Test that missing first_name is rejected."""
        payload = self._valid_payload()
        del payload["first_name"]
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_not_returned_in_response(self, client: AsyncClient):
        """Test that password hash is never returned in the response."""
        response = await client.post(
            "/auth/register",
            json=self._valid_payload(
                email="secretpass@example.com",
                password="MySecretPassword123!",
            ),
        )
        assert response.status_code == 201
        data = response.json()
        assert "hash_password" not in data
        assert "password" not in data
        assert "MySecretPassword123!" not in str(data)

    @pytest.mark.asyncio
    async def test_password_is_hashed(self, client: AsyncClient, db_session):
        """Test that the stored password is hashed, not plaintext."""
        payload = self._valid_payload(password="TestPassword123!")
        await client.post("/auth/register", json=payload)

        from sqlmodel import select

        from app.models.user import User

        result = await db_session.exec(
            select(User).where(User.email == "john.doe@example.com")
        )
        user = result.first()
        assert user is not None
        # Password should be hashed (pwdlib uses $argon2 format)
        assert user.hash_password != "TestPassword123!"
        assert user.hash_password.startswith("$")

    @pytest.mark.asyncio
    async def test_username_auto_generated(self, client: AsyncClient):
        """Test that username is auto-generated from email."""
        response = await client.post(
            "/auth/register",
            json=self._valid_payload(email="newuser@example.com"),
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("username") == "newuser"

    @pytest.mark.asyncio
    async def test_default_role_is_member(self, client: AsyncClient):
        """Test that new users get the MEMBER role by default."""
        response = await client.post(
            "/auth/register",
            json=self._valid_payload(email="defaultrole@example.com"),
        )
        assert response.status_code == 201
        assert response.json()["role"] == "member"
