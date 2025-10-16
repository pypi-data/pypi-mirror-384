# TroveSuite Auth Service

A comprehensive authentication and authorization service for ERP systems. This package provides JWT token validation, user authorization, and permission checking capabilities.

## Features

- **JWT Token Validation**: Secure token decoding and validation
- **User Authorization**: Multi-level authorization with tenant verification
- **Permission Checking**: Hierarchical permission system (organization > business > app > location > resource)
- **Database Integration**: PostgreSQL support with connection pooling
- **Logging**: Comprehensive logging with multiple output formats
- **Azure Integration**: Support for Azure Storage Queues and Managed Identity
- **FastAPI Ready**: Built for FastAPI applications

## Installation

### From GitHub Packages

#### Using pip
```bash
pip install trovesuite-auth-service --index-url https://pypi.org/simple/ --extra-index-url https://pypi.pkg.github.com/deladetech/simple/
```

#### Using Poetry
```bash
# Add GitHub Packages as a source
poetry source add --priority=supplemental github https://pypi.pkg.github.com/deladetech/simple/

# Install the package
poetry add trovesuite-auth-service
```

### From Source

#### Using pip
```bash
git clone https://github.com/deladetech/trovesuite-auth-service.git
cd trovesuite-auth-service
pip install -e .
```

#### Using Poetry
```bash
git clone https://github.com/deladetech/trovesuite-auth-service.git
cd trovesuite-auth-service
poetry install
```

### Development Installation

#### Using pip
```bash
git clone https://github.com/deladetech/trovesuite-auth-service.git
cd trovesuite-auth-service
pip install -e ".[dev]"
```

#### Using Poetry
```bash
git clone https://github.com/deladetech/trovesuite-auth-service.git
cd trovesuite-auth-service
poetry install --with dev
```

## Quick Start

### Basic Usage

```python
from auth_service import AuthService, AuthServiceReadDto
from auth_service.configs import db_settings

# Configure your database settings
db_settings.DB_HOST = "localhost"
db_settings.DB_PORT = 5432
db_settings.DB_NAME = "your_database"
db_settings.DB_USER = "your_user"
db_settings.DB_PASSWORD = "your_password"
db_settings.SECRET_KEY = "your-secret-key"

# Initialize the auth service
auth_service = AuthService()

# Authorize a user
result = auth_service.authorize(user_id="user123", tenant_id="tenant456")

if result.success:
    print("User authorized successfully")
    for role in result.data:
        print(f"Role: {role.role_id}, Permissions: {role.permissions}")
else:
    print(f"Authorization failed: {result.detail}")
```

### JWT Token Decoding

```python
from auth_service import AuthService
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    # Decode and validate token
    user_data = AuthService.decode_token(token)
    user_id = user_data["user_id"]
    tenant_id = user_data["tenant_id"]
    
    # Authorize user
    auth_result = AuthService.authorize(user_id, tenant_id)
    return auth_result
```

### Permission Checking

```python
from auth_service import AuthService

# After getting user roles from authorization
user_roles = auth_result.data

# Check specific permission
has_permission = AuthService.check_permission(
    user_roles=user_roles,
    action="read",
    org_id="org123",
    bus_id="bus456",
    app_id="app789"
)

if has_permission:
    print("User has permission to read from this resource")
```

## Configuration

### Environment Variables

The service uses environment variables for configuration. Set these in your environment or `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DATABASE_URL=postgresql://user:password@localhost:5432/database

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
APP_NAME=Auth Service
ENVIRONMENT=production
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=detailed
LOG_TO_FILE=true

# Table Names (customize as needed)
TENANTS_TABLE=tenants
LOGIN_SETTINGS_TABLE=login_settings
USER_GROUPS_TABLE=user_groups
ASSIGN_ROLES_TABLE=assign_roles
ROLE_PERMISSIONS_TABLE=role_permissions

# Azure (optional - for queue functionality)
STORAGE_ACCOUNT_NAME=your-storage-account
USER_ASSIGNED_MANAGED_IDENTITY=your-managed-identity
```

### Database Schema

The service expects the following database tables:

#### Main Schema Tables
- `tenants` - Tenant information and verification status
- `role_permissions` - Role-permission mappings

#### Tenant Schema Tables (per tenant)
- `login_settings` - User login configurations (working days, suspension status, etc.)
- `user_groups` - User-group memberships
- `assign_roles` - Role assignments to users/groups with resource hierarchy

## API Reference

### AuthService

#### `authorize(user_id: str, tenant_id: str) -> Respons[AuthServiceReadDto]`

Authorizes a user and returns their roles and permissions.

**Parameters:**
- `user_id`: The user identifier
- `tenant_id`: The tenant identifier

**Returns:**
- `Respons[AuthServiceReadDto]`: Authorization result with user roles and permissions

#### `decode_token(token: str) -> dict`

Decodes and validates a JWT token.

**Parameters:**
- `token`: The JWT token to decode

**Returns:**
- `dict`: Token payload with user_id and tenant_id

**Raises:**
- `HTTPException`: If token is invalid

#### `check_permission(user_roles: list, action: str, **kwargs) -> bool`

Checks if a user has a specific permission for a resource.

**Parameters:**
- `user_roles`: List of user roles from authorization
- `action`: The permission action to check
- `org_id`, `bus_id`, `app_id`, `loc_id`, `resource_id`, `shared_resource_id`: Resource identifiers

**Returns:**
- `bool`: True if user has permission, False otherwise

### Data Models

#### `AuthServiceReadDto`

```python
class AuthServiceReadDto(BaseModel):
    org_id: Optional[str] = None
    bus_id: Optional[str] = None 
    app_id: Optional[str] = None 
    loc_id: Optional[str] = None
    shared_resource_id: Optional[str] = None
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    role_id: Optional[str] = None
    tenant_id: Optional[str] = None
    permissions: Optional[List[str]] = None
    resource_id: Optional[str] = None
```

#### `Respons[T]`

```python
class Respons[T](BaseModel):
    detail: Optional[str] = None
    error: Optional[str] = None
    data: Optional[List[T]] = None
    status_code: int = 200
    success: bool = True
    pagination: Optional[PaginationMeta] = None
```

## Development

### Running Tests

#### Using pip
```bash
pytest
```

#### Using Poetry
```bash
poetry run pytest
```

### Code Formatting

#### Using pip
```bash
black auth_service/
```

#### Using Poetry
```bash
poetry run black auth_service/
```

### Type Checking

#### Using pip
```bash
mypy auth_service/
```

#### Using Poetry
```bash
poetry run mypy auth_service/
```

### Linting

#### Using pip
```bash
flake8 auth_service/
```

#### Using Poetry
```bash
poetry run flake8 auth_service/
```

### Poetry Configuration

If you're using Poetry in your project, you can add this package to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
trovesuite-auth-service = "^1.0.0"

[[tool.poetry.source]]
name = "github"
url = "https://pypi.pkg.github.com/deladetech/simple/"
priority = "supplemental"
```

Then run:
```bash
poetry install
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email brightgclt@gmail.com or create an issue in the [GitHub repository](https://github.com/deladetech/trovesuite-auth-service/issues).

## Changelog

### 1.0.0
- Initial release
- JWT token validation
- User authorization with tenant verification
- Hierarchical permission checking
- PostgreSQL database integration
- Comprehensive logging
- Azure integration support
