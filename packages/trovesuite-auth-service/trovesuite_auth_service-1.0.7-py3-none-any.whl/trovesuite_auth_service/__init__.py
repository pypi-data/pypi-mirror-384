"""
Auth Service Package

A comprehensive authentication and authorization service for ERP systems.
Provides JWT token validation, user authorization, and permission checking.
"""

from .auth_service import AuthService
from .auth_base import AuthBase
from .auth_read_dto import AuthServiceReadDto, AuthControllerReadDto

__version__ = "1.0.0"
__author__ = "brightgclt"
__email__ = "brightgclt@gmail.com"

__all__ = [
    "AuthService",
    "AuthBase", 
    "AuthServiceReadDto",
    "AuthControllerReadDto"
]
