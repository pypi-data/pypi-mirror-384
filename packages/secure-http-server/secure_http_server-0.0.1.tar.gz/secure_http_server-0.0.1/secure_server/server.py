"""
Secure HTTP Server implementation.

This module provides the main HTTP server functionality with authentication,
file operations, and security features.
"""

import os
import sys
import base64
import logging
from datetime import datetime
from urllib.parse import unquote, quote
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple, Dict, Any

from secure_server.user_manager import UserManager

logger = logging.getLogger(__name__)


class SecureHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Secure HTTP Request Handler with authentication support.

    This handler implements GET, POST, PUT, and DELETE methods with
    HTTP Basic Authentication and security features.
    """

    protocol_version = "HTTP/1.1"
    user_manager: Optional[UserManager] = None
    debug_mode: bool = False

    def version_string(self) -> str:
        """Return the server software version string."""
        return "SecureHTTPServer/1.0"

    def log_message(self, format: str, *args) -> None:
        """
        Override to use logging module instead of stderr.

        Args:
            format: Format string for the log message
            *args: Arguments to be formatted
        """
        if self.debug_mode:
            logger.info(format % args)

    def _authenticate(self) -> Tuple[bool, Optional[str]]:
        """
        Authenticate the request using HTTP Basic Authentication.

        Returns:
            Tuple of (authenticated, username)
        """
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False, None

        try:
            auth_type, auth_string = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return False, None

            decoded = base64.b64decode(auth_string).decode("utf-8")
            username, password = decoded.split(":", 1)

            if self.user_manager and self.user_manager.authenticate(username, password):
                return True, username
        except Exception as e:
            self._log(f"Authentication error: {e}")

        return False, None

    def _require_auth(self) -> None:
        """Send 401 Unauthorized response."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Secure File Server"')
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "23")
        self.end_headers()
        self.wfile.write(b"Authentication required")

    def _log(self, message: str, username: Optional[str] = None) -> None:
        """
        Log messages with timestamp and optional username.

        Args:
            message: Message to log
            username: Optional username for context
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info = f" [User: {username}]" if username else ""
        log_message = f"[{timestamp}]{user_info} {message}"

        if self.debug_mode:
            logger.debug(log_message)
        else:
            logger.info(log_message)

    def _list_directory(self, directory_path: str) -> str:
        """
        Generate an HTML listing of the directory contents.

        Args:
            directory_path: Path to the directory to list

        Returns:
            HTML string with directory listing
        """
        try:
            entries = os.listdir(directory_path)
            entries.sort(
                key=lambda x: (
                    not os.path.isdir(os.path.join(directory_path, x)),
                    x.lower(),
                )
            )

            rel_path = os.path.relpath(directory_path, os.getcwd())
            if rel_path == ".":
                display_path = "/"
            else:
                display_path = "/" + rel_path.replace(os.sep, "/")

            html = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '<meta charset="utf-8">',
                "<title>Directory listing for {}</title>".format(display_path),
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                "h1 { color: #333; }",
                "table { border-collapse: collapse; width: 100%; }",
                "th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }",
                "tr:hover { background-color: #f5f5f5; }",
                "a { text-decoration: none; color: #0066cc; }",
                "a:hover { text-decoration: underline; }",
                ".dir { font-weight: bold; }",
                ".file { color: #333; }",
                ".size { text-align: right; color: #666; }",
                ".date { color: #666; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Directory listing for {}</h1>".format(display_path),
                "<hr>",
                "<table>",
                "<thead>",
                "<tr><th>Name</th><th>Size</th><th>Modified</th></tr>",
                "</thead>",
                "<tbody>",
            ]

            if directory_path != os.getcwd():
                html.append(
                    '<tr><td colspan="3"><a href="../" class="dir">../</a></td></tr>'
                )

            for entry in entries:
                full_path = os.path.join(directory_path, entry)
                try:
                    stat = os.stat(full_path)
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    if os.path.isdir(full_path):
                        html.append(
                            '<tr><td><a href="{}" class="dir">{}/</a></td>'
                            '<td class="size">-</td>'
                            '<td class="date">{}</td></tr>'.format(
                                quote(entry + "/"), entry, mtime
                            )
                        )
                    else:
                        size = self._format_size(stat.st_size)
                        html.append(
                            '<tr><td><a href="{}" class="file">{}</a></td>'
                            '<td class="size">{}</td>'
                            '<td class="date">{}</td></tr>'.format(
                                quote(entry), entry, size, mtime
                            )
                        )
                except OSError:
                    pass

            html.extend(
                [
                    "</tbody>",
                    "</table>",
                    "<hr>",
                    "<p><small>Secure HTTP Server v1.0</small></p>",
                    "</body>",
                    "</html>",
                ]
            )

            return "\n".join(html)
        except OSError as e:
            return "<html><body><h1>Error</h1><p>{}</p></body></html>".format(str(e))

    def _format_size(self, size: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def do_GET(self) -> None:
        """Handle GET requests with authentication."""
        authenticated, username = self._authenticate()
        if not authenticated:
            self._require_auth()
            self._log("GET: Authentication failed")
            return

        file_path = self._get_file_path()

        if not self._is_safe_path(file_path):
            self._send_response(403, content=b"Access denied: Invalid path")
            self._log(f"GET: Access denied for '{file_path}'", username)
            return

        if os.path.isdir(file_path):
            if not self.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return

            content = self._list_directory(file_path).encode("utf-8")
            self._send_response(
                200,
                content=content,
                headers={"Content-Type": "text/html; charset=utf-8"},
            )
            self._log(
                f"GET: Directory listing for '{file_path}' sent successfully", username
            )
        elif os.path.isfile(file_path):
            content = self._read_file(file_path)
            content_type = self._guess_content_type(file_path)
            self._send_response(
                200, content=content, headers={"Content-Type": content_type}
            )
            self._log(
                f"GET: File '{file_path}' sent successfully ({len(content)} bytes)",
                username,
            )
        else:
            self._send_response(404, content=b"File or directory not found")
            self._log(f"GET: File or directory '{file_path}' not found", username)

    def do_POST(self) -> None:
        """Handle POST requests with authentication."""
        authenticated, username = self._authenticate()
        if not authenticated:
            self._require_auth()
            self._log("POST: Authentication failed")
            return

        file_path = self._get_file_path()

        if not self._is_safe_path(file_path):
            self._send_response(403, content=b"Access denied: Invalid path")
            self._log(f"POST: Access denied for '{file_path}'", username)
            return

        content_length = self._get_content_length()
        data = self._read_request_body(content_length)

        try:
            mode = "ab" if os.path.exists(file_path) else "wb"
            with open(file_path, mode) as file:
                file.write(data)
            self._send_response(201, content=b"Data appended successfully")
            self._log(
                f"POST: Data appended to '{file_path}' ({len(data)} bytes)", username
            )
        except Exception as e:
            self._send_response(500, content=f"Error: {str(e)}".encode())
            self._log(f"POST: Error writing to '{file_path}': {e}", username)

    def do_PUT(self) -> None:
        """Handle PUT requests with authentication."""
        authenticated, username = self._authenticate()
        if not authenticated:
            self._require_auth()
            self._log("PUT: Authentication failed")
            return

        file_path = self._get_file_path()

        if not self._is_safe_path(file_path):
            self._send_response(403, content=b"Access denied: Invalid path")
            self._log(f"PUT: Access denied for '{file_path}'", username)
            return

        content_length = self._get_content_length()
        data = self._read_request_body(content_length)

        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, "wb") as file:
                file.write(data)
            self._send_response(200, content=b"File created/updated successfully")
            self._log(
                f"PUT: File '{file_path}' created/updated ({len(data)} bytes)", username
            )
        except Exception as e:
            self._send_response(500, content=f"Error: {str(e)}".encode())
            self._log(f"PUT: Error writing to '{file_path}': {e}", username)

    def do_DELETE(self) -> None:
        """Handle DELETE requests with authentication."""
        authenticated, username = self._authenticate()
        if not authenticated:
            self._require_auth()
            self._log("DELETE: Authentication failed")
            return

        file_path = self._get_file_path()

        if not self._is_safe_path(file_path):
            self._send_response(403, content=b"Access denied: Invalid path")
            self._log(f"DELETE: Access denied for '{file_path}'", username)
            return

        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                self._send_response(200, content=b"File deleted successfully")
                self._log(f"DELETE: File '{file_path}' deleted", username)
            except Exception as e:
                self._send_response(500, content=f"Error: {str(e)}".encode())
                self._log(f"DELETE: Error deleting '{file_path}': {e}", username)
        else:
            self._send_response(404, content=b"File not found")
            self._log(f"DELETE: File '{file_path}' not found", username)

    def _get_file_path(self) -> str:
        """
        Extract and sanitize the file path from the request URL.

        Returns:
            Sanitized file path
        """
        path = self.path.split("?")[0]
        requested_path = unquote(path.strip("/"))
        base_path = os.getcwd()
        full_path = os.path.join(base_path, requested_path)
        return os.path.normpath(full_path)

    def _is_safe_path(self, path: str) -> bool:
        """
        Check if the path is within the server's root directory.

        Args:
            path: Path to check

        Returns:
            True if path is safe, False otherwise
        """
        base_path = os.path.abspath(os.getcwd())
        requested_path = os.path.abspath(path)
        return requested_path.startswith(base_path)

    def _get_content_length(self) -> int:
        """
        Get the content length from request headers.

        Returns:
            Content length in bytes
        """
        return int(self.headers.get("Content-Length", 0))

    def _read_request_body(self, length: int) -> bytes:
        """
        Read the request body.

        Args:
            length: Number of bytes to read

        Returns:
            Request body as bytes
        """
        return self.rfile.read(length)

    def _read_file(self, file_path: str) -> bytes:
        """
        Read file content in binary mode.

        Args:
            file_path: Path to the file

        Returns:
            File content as bytes
        """
        with open(file_path, "rb") as file:
            return file.read()

    def _guess_content_type(self, file_path: str) -> str:
        """
        Guess the content type based on file extension.

        Args:
            file_path: Path to the file

        Returns:
            Content type string
        """
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".gz": "application/gzip",
            ".tar": "application/x-tar",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".c": "text/x-c",
            ".cpp": "text/x-c++",
            ".java": "text/x-java",
            ".sh": "text/x-shellscript",
        }
        return content_types.get(ext, "application/octet-stream")

    def _send_response(
        self, code: int, content: bytes = b"", headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Send HTTP response.

        Args:
            code: HTTP status code
            content: Response body
            headers: Optional additional headers
        """
        self.send_response(code)
        headers = headers or {}
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Content-Type", headers.get("Content-Type", "text/plain"))
        for key, value in headers.items():
            if key != "Content-Type":
                self.send_header(key, value)
        self.end_headers()
        if content:
            self.wfile.write(content)


class SecureHTTPServer:
    """
    Secure HTTP Server with user authentication.

    This class provides the main server functionality with configuration
    options and lifecycle management.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        users_file: str = "users.json",
        debug: bool = False,
        show_banner: bool = True,
    ):
        """
        Initialize the Secure HTTP Server.

        Args:
            host: Hostname to bind to
            port: Port number to bind to
            users_file: Path to users database file
            debug: Enable debug mode with verbose logging
            show_banner: Show startup banner
        """
        self.host = host
        self.port = port
        self.user_manager = UserManager(users_file)
        self.debug = debug
        self.show_banner = show_banner

        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        SecureHTTPRequestHandler.user_manager = self.user_manager
        SecureHTTPRequestHandler.debug_mode = self.debug

        self.server = HTTPServer((self.host, self.port), SecureHTTPRequestHandler)

    def start(self) -> None:
        """Start the HTTP server and listen for requests."""
        if self.show_banner:
            self._print_banner()

        logger.info(f"Server starting on {self.host}:{self.port}")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.stop()

    def stop(self) -> None:
        """Stop the HTTP server gracefully."""
        logger.info("Shutting down the server...")
        self.server.shutdown()
        self.server.server_close()
        if self.show_banner:
            print("\nServer stopped.")

    def _print_banner(self) -> None:
        """Print the startup banner with server information."""
        print("\n" + "=" * 60)
        print("Secure HTTP Server v1.0")
        print("=" * 60)
        print(f"Server URL: http://{self.host}:{self.port}")
        print(f"Users file: {self.user_manager.users_file}")
        print(f"Active users: {', '.join(self.user_manager.list_users())}")
        print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
        print(f"Working directory: {os.getcwd()}")
        print("=" * 60)
        print("Server is running. Press Ctrl+C to stop.")
        print("=" * 60 + "\n")
