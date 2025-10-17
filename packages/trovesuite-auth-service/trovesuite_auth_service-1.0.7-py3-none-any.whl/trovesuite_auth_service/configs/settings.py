import os
import warnings
from typing import Optional

class Settings:
    """Settings configuration for TroveSuite Auth Service"""

    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://username:password@localhost:5432/database_name"
    )

    # Alternative database configuration
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    DB_NAME: Optional[str] = os.getenv("DB_NAME")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_NAME: str = os.getenv("APP_NAME", "TroveSuite Auth Service")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "detailed")  # detailed, json, simple
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "False").lower() == "false"
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # =============================================================================
    # DATABASE TABLE NAMES
    # =============================================================================
    # Main schema tables
    TENANTS_TABLE: str = os.getenv("TENANTS_TABLE", "tenants")
    ROLE_PERMISSIONS_TABLE: str = os.getenv("ROLE_PERMISSIONS_TABLE", "role_permissions")
    
    # Tenant-specific tables (used in queries with tenant schema)
    LOGIN_SETTINGS_TABLE: str = os.getenv("LOGIN_SETTINGS_TABLE", "login_settings")
    USER_GROUPS_TABLE: str = os.getenv("USER_GROUPS_TABLE", "user_groups")
    ASSIGN_ROLES_TABLE: str = os.getenv("ASSIGN_ROLES_TABLE", "assign_roles")

    # =============================================================================
    # AZURE CONFIGURATION (Optional - for queue functionality)
    # =============================================================================
    STORAGE_ACCOUNT_NAME: str = os.getenv("STORAGE_ACCOUNT_NAME", "")
    USER_ASSIGNED_MANAGED_IDENTITY: str = os.getenv("USER_ASSIGNED_MANAGED_IDENTITY", "")
    
    @property
    def database_url(self) -> str:
        """Get the database URL, either from DATABASE_URL or constructed from individual components"""
        if self.DATABASE_URL != "postgresql://username:password@localhost:5432/database_name":
            return self.DATABASE_URL
        
        # Validate individual components
        if not all([self.DB_USER, self.DB_HOST, self.DB_NAME, self.DB_PASSWORD]):
            missing = []
            if not self.DB_USER:
                missing.append("DB_USER")
            if not self.DB_HOST:
                missing.append("DB_HOST")
            if not self.DB_NAME:
                missing.append("DB_NAME")
            if not self.DB_PASSWORD:
                missing.append("DB_PASSWORD")
            
            raise ValueError(
                f"Database configuration incomplete. Missing environment variables: {', '.join(missing)}. "
                f"Please set these variables or provide a complete DATABASE_URL."
            )
        
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate_configuration(self) -> None:
        """Validate the current configuration and warn about potential issues"""
        warnings_list = []
        
        # Check for default secret key
        if self.SECRET_KEY == "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7":
            warnings_list.append(
                "SECRET_KEY is using the default value. This is insecure for production. "
                "Please set a strong, unique SECRET_KEY environment variable."
            )
        
        # Check for development environment in production-like settings
        if self.ENVIRONMENT == "development" and self.DEBUG is False:
            warnings_list.append(
                "ENVIRONMENT is set to 'development' but DEBUG is False. "
                "Consider setting ENVIRONMENT to 'production' for production deployments."
            )
        
        # Check database configuration
        try:
            self.database_url
        except ValueError as e:
            warnings_list.append(f"Database configuration issue: {str(e)}")
        
        # Check for missing Azure configuration if needed
        if self.ENVIRONMENT == "production" and not self.STORAGE_ACCOUNT_NAME:
            warnings_list.append(
                "STORAGE_ACCOUNT_NAME is not set. Azure queue functionality may not work properly."
            )
        
        # Emit warnings
        for warning in warnings_list:
            warnings.warn(warning, UserWarning)
    
    def get_configuration_summary(self) -> dict:
        """Get a summary of the current configuration (excluding sensitive data)"""
        return {
            "app_name": self.APP_NAME,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "database_host": self.DB_HOST,
            "database_port": self.DB_PORT,
            "database_name": self.DB_NAME,
            "database_user": self.DB_USER,
            "log_level": self.LOG_LEVEL,
            "log_format": self.LOG_FORMAT,
            "log_to_file": self.LOG_TO_FILE,
            "algorithm": self.ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "tenants_table": self.TENANTS_TABLE,
            "role_permissions_table": self.ROLE_PERMISSIONS_TABLE,
            "login_settings_table": self.LOGIN_SETTINGS_TABLE,
            "user_groups_table": self.USER_GROUPS_TABLE,
            "assign_roles_table": self.ASSIGN_ROLES_TABLE,
        }

# Global settings instance
db_settings = Settings()

# Validate configuration on import
try:
    db_settings.validate_configuration()
except Exception as e:
    warnings.warn("Configuration validation failed: %s", str(e), UserWarning)