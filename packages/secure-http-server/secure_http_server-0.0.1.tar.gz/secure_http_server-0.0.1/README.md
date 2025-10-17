# Secure HTTP Server

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, secure HTTP server with authentication and comprehensive file management capabilities.

## Features

- 🔐 **HTTP Basic Authentication** with user management
- 📁 **Full CRUD Operations**: GET, POST, PUT, DELETE
- 🛡️ **Security Features**: Path traversal prevention, password hashing
- 👥 **Multi-user Support** with role-based access
- 📂 **Directory Browsing** with HTML interface
- 🔧 **Command-line Management** for users
- 📝 **Comprehensive Logging** with debug mode
- 🚀 **Zero External Dependencies** for core functionality
- 📦 **Easy Installation** via pip or Debian package (Not supporeted for now!!)

## Table of Contents

- [Installation](#installation)
  - [From PyPI](#from-pypi)
  - [From Source](#from-source)
  - [Debian Package](#debian-package)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Starting the Server](#starting-the-server)
  - [User Management](#user-management)
  - [API Examples](#api-examples)
- [Configuration](#configuration)
- [Security](#security)
- [Development](#development)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Installation

### From PyPI

```bash
pip3 install secure-http-server
```

### From Source

```bash
git clone https://github.com/moncef007/secure-http-server.git
cd secure-http-server
pip3 install -r requirements.txt
make all
```

### Debian Package

```bash
TODO
```

## Quick Start

1. **Start the server** (default port 9000):
   ```bash
   secure-http-server
   ```

2. **Access the server**:
   ```
   http://localhost:9000
   ```
   Default credentials: `admin` / `admin123`

3. **Change the default password**:
   ```bash
   secure-http-server --manage-users
   ```

## Usage

### Starting the Server

```bash
# Basic usage (serves current directory)
secure-http-server

# Specify host and port
secure-http-server --host 0.0.0.0 --port 8080

# Serve a specific directory
secure-http-server --directory /path/to/share

# Use custom users file
secure-http-server --users-file /etc/secure-server/users.json

# Enable debug mode
secure-http-server --debug

# Show help
secure-http-server --help
```

### User Management

#### Interactive Management
```bash
secure-http-server --manage-users
```

#### Command-line Management
```bash
# List all users
secure-http-server --list-users

# Add a new user
secure-http-server --add-user username password role

# Remove a user
secure-http-server --remove-user username
```

### API Examples

#### Upload a File
```bash
curl -u username:password -X PUT \
  --data-binary @local-file.txt \
  http://localhost:9000/uploaded-file.txt
```

#### Download a File
```bash
curl -u username:password \
  http://localhost:9000/uploaded-file.txt \
  -o downloaded-file.txt
```

#### List Directory
```bash
curl -u username:password http://localhost:9000/
```

#### Append to File
```bash
echo "New log entry" | curl -u username:password -X POST \
  --data-binary @- \
  http://localhost:9000/logfile.txt
```

#### Delete a File
```bash
curl -u username:password -X DELETE \
  http://localhost:9000/unwanted-file.txt
```

## Configuration

### Server Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `localhost` | Server bind address |
| `--port` | `9000` | Server port |
| `--directory` | `.` | Directory to serve |
| `--users-file` | `users.json` | Path to users database |
| `--debug` | `False` | Enable debug logging |
| `--no-banner` | `False` | Disable startup banner |

### Users File Format

The users file is a JSON file with the following structure:
```json
{
  "username": {
    "password_hash": "sha256_hash_of_password",
    "role": "user|admin"
  }
}
```

## Security

### Features

- **Authentication**: HTTP Basic Authentication required for all operations
- **Password Security**: SHA-256 hashed passwords (never stored in plain text)
- **Path Traversal Prevention**: All paths are sanitized and restricted to the server root
- **No Directory Traversal**: Requests containing `..` are rejected

## Documentation

### Available Documentation

- **API Documentation**: [docs/API.md](docs/API.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Update documentation as needed
- Keep commits atomic and well-described

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python's built-in `http.server` module
- Thanks to all contributors and testers

## Support

- **Issues**: [GitHub Issues](https://github.com/moncef007/secure-http-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moncef007/secure-http-server/discussions)

---