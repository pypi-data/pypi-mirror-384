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
from trovesuite_auth_service import AuthService, AuthServiceReadDto
from trovesuite_auth_service.configs.settings import db_settings

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
from trovesuite_auth_service import AuthService
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

### Convenience Methods

```python
from trovesuite_auth_service import AuthService

# Get user info directly from token
user_info = AuthService.get_user_info_from_token(token)
print(f"User: {user_info['user_id']}, Tenant: {user_info['tenant_id']}")

# Authorize user directly from token (combines decode + authorize)
auth_result = AuthService.authorize_user_from_token(token)

if auth_result.success:
    # Get all user permissions
    all_permissions = AuthService.get_user_permissions(auth_result.data)
    print(f"User has permissions: {all_permissions}")
    
    # Check if user has any of the required permissions
    has_any = AuthService.has_any_permission(
        auth_result.data, 
        ["read", "write", "admin"]
    )
    
    # Check if user has all required permissions
    has_all = AuthService.has_all_permissions(
        auth_result.data, 
        ["read", "write"]
    )
```

### Permission Checking

```python
from trovesuite_auth_service import AuthService

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

### Quick Configuration Check

```python
from trovesuite_auth_service.configs.settings import db_settings

# Check your configuration
config_summary = db_settings.get_configuration_summary()
print("Current configuration:")
for key, value in config_summary.items():
    print(f"  {key}: {value}")

# The service will automatically validate configuration on import
# and show warnings for potential issues
```

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
- `user_id`: The user identifier (must be a non-empty string)
- `tenant_id`: The tenant identifier (must be a non-empty string)

**Returns:**
- `Respons[AuthServiceReadDto]`: Authorization result with user roles and permissions

**Error Codes:**
- `INVALID_USER_ID`: Invalid or empty user_id
- `INVALID_TENANT_ID`: Invalid or empty tenant_id
- `TENANT_NOT_FOUND`: Tenant doesn't exist or is deleted
- `TENANT_NOT_VERIFIED`: Tenant exists but is not verified
- `USER_NOT_FOUND`: User doesn't exist in tenant or is inactive
- `USER_SUSPENDED`: User account is suspended
- `LOGIN_TIME_RESTRICTED`: Login not allowed at current time

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
- `org_id`, `bus_id`, `app_id`, `resource_id`, `shared_resource_id`: Resource identifiers

**Returns:**
- `bool`: True if user has permission, False otherwise

#### `get_user_info_from_token(token: str) -> dict`

Convenience method to get user information from a JWT token.

**Parameters:**
- `token`: JWT token string

**Returns:**
- `dict`: User information including user_id and tenant_id

#### `authorize_user_from_token(token: str) -> Respons[AuthServiceReadDto]`

Convenience method to authorize a user directly from a JWT token.

**Parameters:**
- `token`: JWT token string

**Returns:**
- `Respons[AuthServiceReadDto]`: Authorization result with user roles and permissions

#### `get_user_permissions(user_roles: list) -> list`

Get all unique permissions for a user across all their roles.

**Parameters:**
- `user_roles`: List of user roles from authorization

**Returns:**
- `list`: Unique list of permissions

#### `has_any_permission(user_roles: list, required_permissions: list) -> bool`

Check if user has any of the required permissions.

**Parameters:**
- `user_roles`: List of user roles from authorization
- `required_permissions`: List of permissions to check for

**Returns:**
- `bool`: True if user has any of the required permissions

#### `has_all_permissions(user_roles: list, required_permissions: list) -> bool`

Check if user has all of the required permissions.

**Parameters:**
- `user_roles`: List of user roles from authorization
- `required_permissions`: List of permissions to check for

**Returns:**
- `bool`: True if user has all of the required permissions

### Data Models

#### `AuthServiceReadDto`

```python
class AuthServiceReadDto(BaseModel):
    org_id: Optional[str] = None
    bus_id: Optional[str] = None 
    app_id: Optional[str] = None 
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

## Error Handling

The service provides comprehensive error handling with specific error codes and user-friendly messages:

### Common Error Scenarios

```python
from trovesuite_auth_service import AuthService

# Example: Handle authorization errors
result = AuthService.authorize("user123", "tenant456")

if not result.success:
    if result.error == "TENANT_NOT_FOUND":
        print("Tenant doesn't exist")
    elif result.error == "USER_SUSPENDED":
        print("User account is suspended")
    elif result.error == "LOGIN_TIME_RESTRICTED":
        print("Login not allowed at this time")
    else:
        print(f"Authorization failed: {result.detail}")
else:
    print("Authorization successful!")
```

### Best Practices

1. **Always check the `success` field** before accessing `data`
2. **Use specific error codes** for programmatic error handling
3. **Display user-friendly messages** from the `detail` field
4. **Log errors** for debugging purposes
5. **Validate input parameters** before calling service methods

### Configuration Validation

The service automatically validates configuration on import and shows warnings for potential issues:

```python
# Configuration validation happens automatically
from trovesuite_auth_service.configs.settings import db_settings

# Check configuration summary
config = db_settings.get_configuration_summary()
print("Configuration loaded successfully")

# Common warnings you might see:
# - Default SECRET_KEY in production
# - Missing database configuration
# - Inconsistent environment settings
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
black trovesuite_auth_service/
```

#### Using Poetry
```bash
poetry run black trovesuite_auth_service/
```

### Type Checking

#### Using pip
```bash
mypy trovesuite_auth_service/
```

#### Using Poetry
```bash
poetry run mypy trovesuite_auth_service/
```

### Linting

#### Using pip
```bash
flake8 trovesuite_auth_service/
```

#### Using Poetry
```bash
poetry run flake8 trovesuite_auth_service/
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
