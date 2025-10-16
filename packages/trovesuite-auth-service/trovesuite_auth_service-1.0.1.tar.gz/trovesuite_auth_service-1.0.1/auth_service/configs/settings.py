import os

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
    DB_USER: str = os.getenv("DB_USER")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
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
        
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Global settings instance
db_settings = Settings()