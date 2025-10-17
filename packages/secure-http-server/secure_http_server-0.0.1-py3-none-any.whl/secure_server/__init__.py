#!/usr/bin/env python3
"""
Main entry point for Secure HTTP Server.

This module provides the command-line interface and main function
for running the server or managing users.
"""

import os
import argparse
import sys
from pathlib import Path

from secure_server.server import SecureHTTPServer
from secure_server.user_manager import UserManager

__version__ = "0.0.1"


def create_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="secure-http-server",
        description="Secure HTTP Server with authentication supporting " \
                    "GET, POST, PUT, and DELETE methods.",
        epilog="For more information, " \
                 "visit: https://github.com/moncef007/secure-http-server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Hostname to bind the server to (default: localhost)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=9000,
        help="Port number to bind the server to (default: 9000)",
    )

    parser.add_argument(
        "--users-file",
        type=str,
        default="users.json",
        help="Path to users file (default: users.json)",
    )

    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=".",
        help="Directory to serve (default: current directory)",
    )

    parser.add_argument(
        "--manage-users",
        action="store_true",
        help="Manage users (add, remove, change password)",
    )

    parser.add_argument(
        "--add-user",
        nargs=3,
        metavar=("USERNAME", "PASSWORD", "ROLE"),
        help="Add a user non-interactively",
    )

    parser.add_argument(
        "--remove-user", metavar="USERNAME", help="Remove a user non-interactively"
    )

    parser.add_argument("--list-users", action="store_true", help="List all users")

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose logging"
    )

    parser.add_argument(
        "--no-banner", action="store_true", help="Disable startup banner"
    )

    return parser


def manage_users_interactive(users_file):
    """Interactive user management menu."""
    user_manager = UserManager(users_file)

    while True:
        print("\n" + "=" * 40)
        print("User Management")
        print("=" * 40)
        print("1. List users")
        print("2. Add user")
        print("3. Remove user")
        print("4. Change password")
        print("5. Exit")
        print("=" * 40)

        try:
            choice = input("\nEnter your choice (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting user management...")
            break

        if choice == "1":
            users = user_manager.list_users()
            print(f"\nActive users: {', '.join(users)}")

        elif choice == "2":
            try:
                username = input("Enter username: ").strip()
                password = input("Enter password: ").strip()
                role = input("Enter role (admin/user) [user]: ").strip() or "user"
                _, message = user_manager.add_user(username, password, role)
                print(f"\n{message}")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled")

        elif choice == "3":
            try:
                username = input("Enter username to remove: ").strip()
                _, message = user_manager.remove_user(username)
                print(f"\n{message}")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled")

        elif choice == "4":
            try:
                username = input("Enter username: ").strip()
                old_password = input("Enter old password: ").strip()
                new_password = input("Enter new password: ").strip()
                _, message = user_manager.change_password(
                    username, old_password, new_password
                )
                print(f"\n{message}")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled")

        elif choice == "5":
            break

        else:
            print("\nInvalid choice. Please try again.")


def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)

    os.chdir(directory)

    if args.list_users:
        user_manager = UserManager(args.users_file)
        users = user_manager.list_users()
        print("Active users:")
        for user in users:
            print(f"  - {user}")
        sys.exit(0)

    if args.add_user:
        username, password, role = args.add_user
        user_manager = UserManager(args.users_file)
        success, message = user_manager.add_user(username, password, role)
        print(message)
        sys.exit(0 if success else 1)

    if args.remove_user:
        user_manager = UserManager(args.users_file)
        success, message = user_manager.remove_user(args.remove_user)
        print(message)
        sys.exit(0 if success else 1)

    if args.manage_users:
        manage_users_interactive(args.users_file)
        sys.exit(0)

    try:
        server = SecureHTTPServer(
            host=args.host,
            port=args.port,
            users_file=args.users_file,
            debug=args.debug,
            show_banner=not args.no_banner,
        )
        server.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
