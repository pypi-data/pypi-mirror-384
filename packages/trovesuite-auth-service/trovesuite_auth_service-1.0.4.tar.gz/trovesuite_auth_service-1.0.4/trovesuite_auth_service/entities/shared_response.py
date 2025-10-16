from pydantic import BaseModel
from typing import Optional, List, Any, TypeVar, Generic

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int
    size: int
    total: int
    has_next: bool

T = TypeVar('T')

class Respons(BaseModel, Generic[T]):
    detail: Optional[str] = None
    error: Optional[str] = None
    data: Optional[List[T]] = None
    status_code: int = 200
    success: bool = True
    pagination: Optional[PaginationMeta] = None


class ResponseException(Exception):
    """Custom exception that carries a response model"""
    
    def __init__(self, message: str, response: Respons):
        self.message = message
        self.response = response
        super().__init__(self.message)


def create_error_response(
    error_message: str,
    status_code: int = 500,
    details: str = "An error occurred",
    data: Optional[List[Any]] = None
) -> dict:
    """Helper function to create error response dictionary"""
    return {
        "detail": details,
        "error": error_message,
        "data": data or [],
        "status_code": status_code,
        "success": False
    }


def raise_with_response(
    message: str,
    status_code: int = 500,
    details: str = "An error occurred",
    data: Optional[List[Any]] = None
) -> None:
    """Helper function to raise ResponseException with error response"""
    error_response = Respons(
        detail=details,
        error=message,
        data=data or [],
        status_code=status_code,
        success=False
    )
    raise ResponseException(message, error_response)
