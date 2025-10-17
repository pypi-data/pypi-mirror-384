"""
FastAPI Mock Service - Professional mock service library with load testing infrastructure

A comprehensive library for creating FastAPI-based mock services with:
- Built-in Prometheus metrics
- Real-time dashboard with charts
- Load testing infrastructure
- Automatic parameter validation
- Flexible response configuration
- Database integration for test results

Usage:
    ```python
    from fastapi_mock_service import MockService

    # Create mock service
    mock = MockService()

    # Add endpoint with decorator
    @mock.get("/api/users/{user_id}")
    def get_user(user_id: int):
        return {"id": user_id, "name": "John Doe"}

    # Run the service
    if __name__ == "__main__":
        mock.run()
    ```
"""

from .mock_service import MockService

__version__ = "1.0.7"
__author__ = "Denis Sviridov"
__email__ = "Sviridov.DS@bk.ru"

__all__ = [
    "MockService",
]
