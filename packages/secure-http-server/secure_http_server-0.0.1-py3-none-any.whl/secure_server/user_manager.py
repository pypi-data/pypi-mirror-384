import hashlib
import json
import os

class UserManager:
    """
    Manages user authentication with hashed passwords.
    """

    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = self._load_users()

    def _load_users(self):
        """
        Load users from JSON file
        """
        if os.path.exists(self.users_file):
            with open(self.users_file, "r") as f:
                return json.load(f)
        else:
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin",
                }
            }
            self._save_users(default_users)
            print("Created default user - Username: admin, Password: admin123")
            print("Please change the default password immediately!")
            return default_users

    def _save_users(self, users):
        """
        Save users to JSON file
        """
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2)

    def _hash_password(self, password):
        """
        Hash password using SHA-256
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """
        Authenticate user with username and password
        """
        if username in self.users:
            password_hash = self._hash_password(password)
            return self.users[username]["password_hash"] == password_hash
        return False

    def add_user(self, username, password, role="user"):
        """
        Add a new user
        """
        if username in self.users:
            return False, "User already exists"
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
        }
        self._save_users(self.users)
        return True, "User added successfully"

    def remove_user(self, username):
        """
        Remove a user
        """
        if username not in self.users:
            return False, "User not found"
        if username == "admin":
            return False, "Cannot remove admin user"
        del self.users[username]
        self._save_users(self.users)
        return True, "User removed successfully"

    def change_password(self, username, old_password, new_password):
        """
        Change user password
        """
        if not self.authenticate(username, old_password):
            return False, "Invalid credentials"
        self.users[username]["password_hash"] = self._hash_password(new_password)
        self._save_users(self.users)
        return True, "Password changed successfully"

    def list_users(self):
        """List all usernames."""
        return list(self.users.keys())
