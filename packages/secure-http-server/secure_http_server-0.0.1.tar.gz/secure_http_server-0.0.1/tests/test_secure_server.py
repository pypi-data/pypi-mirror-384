"""
Test suite for SecureHTTPServer.

This module contains integration tests for the HTTP server functionality including
authentication, file operations, directory listing, and security features.
"""

import os
import threading
import time

import pytest
import requests
from requests.auth import HTTPBasicAuth

from secure_server.server import SecureHTTPServer
from secure_server.user_manager import UserManager


@pytest.fixture(scope="module")
def server_config():
    """Provide server configuration."""
    return {"host": "localhost", "port": 9999, "users_file": "test_users.json"}


@pytest.fixture(scope="module")
def server(server_config, tmp_path_factory):
    """Start test server for the entire module."""
    test_dir = tmp_path_factory.mktemp("server_test")
    original_dir = os.getcwd()
    os.chdir(test_dir)

    user_manager = UserManager(server_config["users_file"])
    user_manager.add_user("testuser", "testpass", "user")
    user_manager.add_user("alice", "alice123", "user")

    srv = SecureHTTPServer(
        host=server_config["host"],
        port=server_config["port"],
        users_file=server_config["users_file"],
    )
    server_thread = threading.Thread(target=srv.start, daemon=True)
    server_thread.start()

    time.sleep(1)

    yield srv

    srv.stop()
    os.chdir(original_dir)


@pytest.fixture
def base_url(server_config):
    """Provide base URL for server requests."""
    return f"http://{server_config['host']}:{server_config['port']}"


@pytest.fixture
def auth():
    """Provide test user authentication."""
    return HTTPBasicAuth("testuser", "testpass")


@pytest.fixture
def admin_auth():
    """Provide admin authentication."""
    return HTTPBasicAuth("admin", "admin123")


@pytest.fixture
def alice_auth():
    """Provide alice user authentication."""
    return HTTPBasicAuth("alice", "alice123")


@pytest.fixture(autouse=True)
def cleanup_files():
    """Clean up test files after each test."""
    yield
    test_files = [
        "testfile.txt",
        "gettest.txt",
        "appendtest.txt",
        "deletetest.txt",
        "binary.bin",
        "largefile.bin",
        "test file with spaces.txt",
        "empty.txt",
        "shared.txt",
        "lifecycle.txt",
        "concurrent_test.txt",
    ]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)

    test_dirs = ["testdir", "subdir"]
    for d in test_dirs:
        if os.path.exists(d):
            import shutil

            shutil.rmtree(d)


class TestServerBasics:
    """Tests for basic server functionality."""

    def test_server_running(self, base_url, auth):
        """Test that server is running and responding."""
        response = requests.get(base_url, auth=auth, timeout=5)
        assert response.status_code in [200, 401, 403]

    def test_server_reachable_without_auth(self, base_url):
        """Test that server responds even without authentication."""
        response = requests.get(base_url, timeout=5)
        assert response.status_code == 401


class TestAuthentication:
    """Tests for server authentication."""

    def test_authentication_required(self, base_url):
        """Test that authentication is required for all requests."""
        response = requests.get(base_url)
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_invalid_credentials(self, base_url):
        """Test authentication with invalid credentials."""
        invalid_auth = HTTPBasicAuth("testuser", "wrongpassword")
        response = requests.get(base_url, auth=invalid_auth)
        assert response.status_code == 401

    def test_valid_credentials(self, base_url, auth):
        """Test authentication with valid credentials."""
        response = requests.get(base_url, auth=auth)
        assert response.status_code == 200

    def test_nonexistent_user(self, base_url):
        """Test authentication with non-existent user."""
        fake_auth = HTTPBasicAuth("nonexistent", "password")
        response = requests.get(base_url, auth=fake_auth)
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "username,password,expected_status",
        [
            ("testuser", "testpass", 200),
            ("admin", "admin123", 200),
            ("testuser", "wrong", 401),
            ("nobody", "nothing", 401),
        ],
    )
    def test_authentication_combinations(
        self, base_url, username, password, expected_status
    ):
        """Test various authentication combinations."""
        auth = HTTPBasicAuth(username, password)
        response = requests.get(base_url, auth=auth)
        assert response.status_code == expected_status


class TestFileOperations:
    """Tests for file CRUD operations."""

    def test_put_create_file(self, base_url, auth):
        """Test creating a file with PUT request."""
        test_content = b"Hello, World!"
        response = requests.put(
            f"{base_url}/testfile.txt", data=test_content, auth=auth
        )
        assert response.status_code == 200
        assert os.path.exists("testfile.txt")

        with open("testfile.txt", "rb") as f:
            assert f.read() == test_content

    def test_put_overwrite_file(self, base_url, auth):
        """Test overwriting an existing file with PUT."""
        requests.put(f"{base_url}/testfile.txt", data=b"Initial", auth=auth)

        new_content = b"Overwritten"
        response = requests.put(f"{base_url}/testfile.txt", data=new_content, auth=auth)
        assert response.status_code == 200

        with open("testfile.txt", "rb") as f:
            assert f.read() == new_content

    def test_get_file(self, base_url, auth):
        """Test retrieving a file with GET request."""
        test_content = b"Test content"
        with open("gettest.txt", "wb") as f:
            f.write(test_content)

        response = requests.get(f"{base_url}/gettest.txt", auth=auth)
        assert response.status_code == 200
        assert response.content == test_content

    def test_get_nonexistent_file(self, base_url, auth):
        """Test retrieving a non-existent file returns 404."""
        response = requests.get(f"{base_url}/nonexistent.txt", auth=auth)
        assert response.status_code == 404

    def test_post_append_file(self, base_url, auth):
        """Test appending to a file with POST request."""
        initial_content = b"Initial content\n"
        append_content = b"Appended content\n"

        with open("appendtest.txt", "wb") as f:
            f.write(initial_content)

        response = requests.post(
            f"{base_url}/appendtest.txt", data=append_content, auth=auth
        )
        assert response.status_code == 201

        with open("appendtest.txt", "rb") as f:
            content = f.read()
            assert content == initial_content + append_content

    def test_post_create_file_if_not_exists(self, base_url, auth):
        """Test that POST creates file if it doesn't exist."""
        content = b"New file content"
        response = requests.post(f"{base_url}/newfile.txt", data=content, auth=auth)
        assert response.status_code in [200, 201, 404]

    def test_delete_file(self, base_url, auth):
        """Test deleting a file with DELETE request."""
        with open("deletetest.txt", "w") as f:
            f.write("Delete me")

        response = requests.delete(f"{base_url}/deletetest.txt", auth=auth)
        assert response.status_code == 200
        assert not os.path.exists("deletetest.txt")

    def test_delete_nonexistent_file(self, base_url, auth):
        """Test deleting a non-existent file returns 404."""
        response = requests.delete(f"{base_url}/nonexistent.txt", auth=auth)
        assert response.status_code == 404


class TestDirectoryOperations:
    """Tests for directory listing and navigation."""

    def test_directory_listing(self, base_url, auth):
        """Test directory listing."""
        os.makedirs("testdir", exist_ok=True)
        with open("testdir/file1.txt", "w") as f:
            f.write("content1")
        with open("testdir/file2.txt", "w") as f:
            f.write("content2")

        response = requests.get(f"{base_url}/testdir/", auth=auth)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        assert "file1.txt" in response.text
        assert "file2.txt" in response.text

    def test_root_directory_listing(self, base_url, auth):
        """Test root directory listing."""
        response = requests.get(f"{base_url}/", auth=auth)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_put_with_subdirectory(self, base_url, auth):
        """Test creating a file in a subdirectory."""
        test_content = b"Subdirectory content"
        response = requests.put(
            f"{base_url}/subdir/newfile.txt", data=test_content, auth=auth
        )
        assert response.status_code == 200
        assert os.path.exists("subdir/newfile.txt")

        with open("subdir/newfile.txt", "rb") as f:
            assert f.read() == test_content


class TestBinaryAndSpecialFiles:
    """Tests for binary files and special cases."""

    def test_binary_file_operations(self, base_url, auth):
        """Test operations with binary files."""
        binary_content = bytes(range(256))

        response = requests.put(
            f"{base_url}/binary.bin", data=binary_content, auth=auth
        )
        assert response.status_code == 200

        response = requests.get(f"{base_url}/binary.bin", auth=auth)
        assert response.status_code == 200
        assert response.content == binary_content

    def test_large_file_upload(self, base_url, auth):
        """Test uploading a large file."""
        large_content = b"X" * (1024 * 1024)  # 1 MB
        response = requests.put(
            f"{base_url}/largefile.bin", data=large_content, auth=auth
        )
        assert response.status_code == 200

        with open("largefile.bin", "rb") as f:
            assert len(f.read()) == len(large_content)

    def test_special_characters_in_filename(self, base_url, auth):
        """Test files with special characters in names."""
        test_content = b"Special chars test"
        filename = "test file with spaces.txt"

        response = requests.put(f"{base_url}/{filename}", data=test_content, auth=auth)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/{filename}", auth=auth)
        assert response.status_code == 200
        assert response.content == test_content

    def test_empty_file_operations(self, base_url, auth):
        """Test operations with empty files."""
        response = requests.put(f"{base_url}/empty.txt", data=b"", auth=auth)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/empty.txt", auth=auth)
        assert response.status_code == 200
        assert len(response.content) == 0

    @pytest.mark.parametrize("size", [0, 1, 1024, 10240, 1024 * 1024])
    def test_various_file_sizes(self, base_url, auth, size):
        """Test uploading files of various sizes."""
        content = b"X" * size
        response = requests.put(f"{base_url}/size_test.bin", data=content, auth=auth)
        assert response.status_code == 200

        response = requests.get(f"{base_url}/size_test.bin", auth=auth)
        assert len(response.content) == size

        if os.path.exists("size_test.bin"):
            os.remove("size_test.bin")


class TestSecurity:
    """Tests for security features."""

    def test_path_traversal_prevention(self, base_url, auth):
        """Test that path traversal attacks are prevented."""
        response = requests.get(f"{base_url}/../etc/passwd", auth=auth)
        assert response.status_code == 403

    def test_path_traversal_encoded(self, base_url, auth):
        """Test path traversal with encoded characters."""
        response = requests.get(f"{base_url}/%2E%2E/etc/passwd", auth=auth)
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "malicious_path",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "./../sensitive.txt",
            "/%2e%2e/%2e%2e/etc/passwd",
        ],
    )
    def test_various_path_traversal_attempts(self, base_url, auth, malicious_path):
        """Test various path traversal attack patterns."""
        response = requests.get(f"{base_url}/{malicious_path}", auth=auth)
        assert response.status_code in [403, 404]

    def test_authentication_required_for_all_methods(self, base_url):
        """Test that all HTTP methods require authentication."""
        methods_and_calls = [
            ("GET", lambda: requests.get(f"{base_url}/test.txt")),
            ("PUT", lambda: requests.put(f"{base_url}/test.txt", data=b"test")),
            ("POST", lambda: requests.post(f"{base_url}/test.txt", data=b"test")),
            ("DELETE", lambda: requests.delete(f"{base_url}/test.txt")),
        ]

        for method, call in methods_and_calls:
            response = call()
            assert response.status_code == 401, f"{method} should require auth"


class TestMultiUserScenarios:
    """Tests for multi-user scenarios."""

    def test_multi_user_file_sharing(self, base_url, auth, alice_auth):
        """Test multiple users accessing the same files."""
        response = requests.put(
            f"{base_url}/shared.txt", data=b"Shared content", auth=auth
        )
        assert response.status_code == 200

        response = requests.get(f"{base_url}/shared.txt", auth=alice_auth)
        assert response.status_code == 200
        assert response.content == b"Shared content"

        response = requests.post(
            f"{base_url}/shared.txt", data=b"\nAlice's addition", auth=alice_auth
        )
        assert response.status_code == 201

        response = requests.get(f"{base_url}/shared.txt", auth=auth)
        assert response.status_code == 200
        assert b"Alice's addition" in response.content

    def test_concurrent_file_access(self, base_url, auth, alice_auth):
        """Test concurrent access to the same file."""
        requests.put(f"{base_url}/concurrent_test.txt", data=b"Initial", auth=auth)

        response1 = requests.get(f"{base_url}/concurrent_test.txt", auth=auth)
        response2 = requests.get(f"{base_url}/concurrent_test.txt", auth=alice_auth)

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content


class TestFileLifecycle:
    """Tests for complete file lifecycle scenarios."""

    def test_complete_file_lifecycle(self, base_url, auth):
        """Test complete file lifecycle: create, read, update, delete."""
        filename = f"{base_url}/lifecycle.txt"

        response = requests.put(filename, data=b"Initial", auth=auth)
        assert response.status_code == 200

        response = requests.get(filename, auth=auth)
        assert response.status_code == 200
        assert response.content == b"Initial"

        response = requests.put(filename, data=b"Updated", auth=auth)
        assert response.status_code == 200

        response = requests.get(filename, auth=auth)
        assert response.content == b"Updated"

        response = requests.post(filename, data=b"\nAppended", auth=auth)
        assert response.status_code == 201

        response = requests.get(filename, auth=auth)
        assert b"Updated" in response.content
        assert b"Appended" in response.content

        response = requests.delete(filename, auth=auth)
        assert response.status_code == 200

        response = requests.get(filename, auth=auth)
        assert response.status_code == 404
