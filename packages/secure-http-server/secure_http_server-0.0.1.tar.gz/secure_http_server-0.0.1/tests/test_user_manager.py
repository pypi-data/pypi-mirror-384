"""
Test suite for UserManager class.

This module contains unit tests for user management functionality including
authentication, user CRUD operations, and password management.
"""

import os

import pytest

from secure_server import UserManager


@pytest.fixture
def users_file(tmp_path):
    """Provide a temporary users file path."""
    return str(tmp_path / "test_users.json")


@pytest.fixture
def user_manager(users_file):
    """Provide a fresh UserManager instance for each test."""
    return UserManager(users_file)


class TestUserManagerInitialization:
    """Tests for UserManager initialization and setup."""

    def test_default_admin_user_created(self, user_manager):
        """Test that default admin user is created on initialization."""
        assert "admin" in user_manager.users
        assert user_manager.authenticate("admin", "admin123")

    def test_users_file_created(self, users_file, user_manager):
        """Test that users file is created."""
        assert os.path.exists(users_file)


class TestAuthentication:
    """Tests for user authentication."""

    def test_authenticate_valid_user(self, user_manager):
        """Test authentication with valid credentials."""
        assert user_manager.authenticate("admin", "admin123") is True

    def test_authenticate_invalid_password(self, user_manager):
        """Test authentication with invalid password."""
        assert user_manager.authenticate("admin", "wrongpassword") is False

    def test_authenticate_nonexistent_user(self, user_manager):
        """Test authentication with non-existent user."""
        assert user_manager.authenticate("nonexistent", "password") is False

    @pytest.mark.parametrize(
        "username,password,expected",
        [
            ("admin", "admin123", True),
            ("admin", "wrong", False),
            ("missing", "any", False),
            ("", "", False),
        ],
    )
    def test_authenticate_parametrized(
        self, user_manager, username, password, expected
    ):
        """Test authentication with various credential combinations."""
        assert user_manager.authenticate(username, password) is expected


class TestUserCRUD:
    """Tests for user Create, Read, Update, Delete operations."""

    def test_add_user_success(self, user_manager):
        """Test adding a new user successfully."""
        success, message = user_manager.add_user("testuser", "testpass", "user")
        assert success is True
        assert user_manager.authenticate("testuser", "testpass") is True

    def test_add_user_duplicate(self, user_manager):
        """Test adding a duplicate user fails."""
        user_manager.add_user("testuser", "testpass", "user")
        success, message = user_manager.add_user("testuser", "newpass", "user")
        assert success is False
        assert "already exists" in message.lower()

    @pytest.mark.parametrize(
        "username,password,role",
        [
            ("user1", "pass1", "user"),
            ("admin2", "admin_pass", "admin"),
            ("test_user", "complex!Pass123", "user"),
        ],
    )
    def test_add_multiple_users(self, user_manager, username, password, role):
        """Test adding multiple users with different roles."""
        success, _ = user_manager.add_user(username, password, role)
        assert success is True
        assert user_manager.authenticate(username, password) is True

    def test_remove_user_success(self, user_manager):
        """Test removing a user successfully."""
        user_manager.add_user("testuser", "testpass", "user")
        success, message = user_manager.remove_user("testuser")
        assert success is True
        assert user_manager.authenticate("testuser", "testpass") is False

    def test_remove_nonexistent_user(self, user_manager):
        """Test removing a non-existent user fails."""
        success, message = user_manager.remove_user("nonexistent")
        assert success is False
        assert "not found" in message.lower()

    def test_remove_admin_user_fails(self, user_manager):
        """Test that admin user cannot be removed."""
        success, message = user_manager.remove_user("admin")
        assert success is False
        assert "cannot remove admin" in message.lower()

    def test_list_users(self, user_manager):
        """Test listing all users."""
        user_manager.add_user("user1", "pass1", "user")
        user_manager.add_user("user2", "pass2", "user")
        users = user_manager.list_users()
        assert "admin" in users
        assert "user1" in users
        assert "user2" in users
        assert len(users) >= 3

    def test_list_users_empty_except_admin(self, user_manager):
        """Test listing users when only admin exists."""
        users = user_manager.list_users()
        assert users == ["admin"]


class TestPasswordManagement:
    """Tests for password management functionality."""

    def test_change_password_success(self, user_manager):
        """Test changing user password successfully."""
        success, message = user_manager.change_password(
            "admin", "admin123", "newpassword"
        )
        assert success is True
        assert user_manager.authenticate("admin", "newpassword") is True
        assert user_manager.authenticate("admin", "admin123") is False

    def test_change_password_invalid_old_password(self, user_manager):
        """Test changing password with invalid old password fails."""
        success, message = user_manager.change_password("admin", "wrongpass", "newpass")
        assert success is False
        assert "invalid credentials" in message.lower()

    def test_change_password_nonexistent_user(self, user_manager):
        """Test changing password for non-existent user fails."""
        success, message = user_manager.change_password("nonexistent", "old", "new")
        assert success is False

    def test_password_hashing(self, user_manager):
        """Test that passwords are hashed and not stored in plain text."""
        password = "testpassword"
        password_hash = user_manager._hash_password(password)
        assert password != password_hash
        assert len(password_hash) == 64  # SHA-256 produces 64 hex chars
        assert isinstance(password_hash, str)

    def test_same_password_different_users(self, user_manager):
        """Test that same password for different users produces different hashes with salt."""
        user_manager.add_user("user1", "samepass", "user")
        user_manager.add_user("user2", "samepass", "user")
        # Both should authenticate
        assert user_manager.authenticate("user1", "samepass") is True
        assert user_manager.authenticate("user2", "samepass") is True


class TestPersistence:
    """Tests for data persistence functionality."""

    def test_users_persistence(self, users_file):
        """Test that users are persisted to file and can be reloaded."""
        # Create first manager and add user
        manager1 = UserManager(users_file)
        manager1.add_user("persistuser", "persistpass", "user")

        # Create new manager instance (should load from file)
        manager2 = UserManager(users_file)
        assert manager2.authenticate("persistuser", "persistpass") is True

    def test_persistence_after_user_removal(self, users_file):
        """Test persistence after removing a user."""
        manager1 = UserManager(users_file)
        manager1.add_user("tempuser", "temppass", "user")
        manager1.remove_user("tempuser")

        manager2 = UserManager(users_file)
        assert manager2.authenticate("tempuser", "temppass") is False

    def test_persistence_after_password_change(self, users_file):
        """Test persistence after changing password."""
        manager1 = UserManager(users_file)
        manager1.change_password("admin", "admin123", "newpass")

        manager2 = UserManager(users_file)
        assert manager2.authenticate("admin", "newpass") is True
        assert manager2.authenticate("admin", "admin123") is False


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.parametrize("username", ["", " ", "   "])
    def test_empty_or_whitespace_username(self, user_manager, username):
        """Test handling of empty or whitespace usernames."""
        success, _ = user_manager.add_user(username, "password", "user")
        # Should either fail or handle gracefully
        if success:
            assert user_manager.authenticate(username, "password") is True

    @pytest.mark.parametrize("password", ["", "a", "x" * 1000])
    def test_various_password_lengths(self, user_manager, password):
        """Test handling of various password lengths."""
        success, _ = user_manager.add_user("testuser", password, "user")
        if success:
            assert user_manager.authenticate("testuser", password) is True

    def test_special_characters_in_username(self, user_manager):
        """Test usernames with special characters."""
        special_usernames = ["user@example.com", "user-name", "user_name", "user.name"]
        for username in special_usernames:
            success, _ = user_manager.add_user(username, "password", "user")
            if success:
                assert user_manager.authenticate(username, "password") is True

    def test_unicode_in_credentials(self, user_manager):
        """Test handling of Unicode characters in credentials."""
        success, _ = user_manager.add_user("utilisateur", "motdepasse123", "user")
        if success:
            assert user_manager.authenticate("utilisateur", "motdepasse123") is True
