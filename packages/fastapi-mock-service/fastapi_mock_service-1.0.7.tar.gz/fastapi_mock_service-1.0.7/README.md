# FastAPI Mock Service

[![PyPI version](https://badge.fury.io/py/fastapi-mock-service.svg)](https://badge.fury.io/py/fastapi-mock-service)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Professional mock service library with load testing infrastructure for FastAPI. Create powerful mock APIs with built-in
monitoring, metrics collection, and interactive dashboard.

## 🚀 Features

- **Easy Mock Creation**: Simple decorators to create mock endpoints
- **Built-in Dashboard**: Real-time monitoring with interactive web interface
- **Prometheus Metrics**: Comprehensive metrics collection for performance analysis
- **Load Testing Support**: Built-in infrastructure for load testing mock services
- **Database Integration**: SQLite database for test results storage
- **Flexible Response Configuration**: Support for complex response scenarios
- **CLI Tool**: Command-line interface for quick setup and management
- **Auto Validation**: Automatic parameter validation with error handling

## 📦 Installation

```bash
pip install fastapi-mock-service
```

## 🎯 Quick Start

### 1. Basic Usage

```python
from fastapi_mock_service import MockService
from pydantic import BaseModel

# Create mock service
mock = MockService()

class User(BaseModel):
    id: int
    name: str
    email: str

# Create mock endpoints
@mock.get("/api/users/{user_id}")
def get_user(user_id: int):
    return User(
        id=user_id,
        name=f"User {user_id}",
        email=f"user{user_id}@example.com"
    )

@mock.post("/api/users")
def create_user(user: User):
    return {"message": "User created", "user": user}

if __name__ == "__main__":
    mock.run()
```

### 2. Using CLI

```bash
# Create example file
fastapi-mock init my_mock.py

# Create advanced example with error codes
fastapi-mock init advanced_mock.py --advanced

# Run mock service
fastapi-mock run my_mock.py

# Run on custom port
fastapi-mock run my_mock.py --port 9000

# Test session management (independent of admin interface)
fastapi-mock test start --name "Load Test"    # Start test session
fastapi-mock test stop --session-id <id>      # Stop specific test session
fastapi-mock test status                      # Get current test session status
fastapi-mock test stop --force                # Force stop current test

# Mock endpoint control (independent of test sessions)
fastapi-mock mock activate                    # Activate mock endpoints
fastapi-mock mock deactivate                  # Deactivate mock endpoints
fastapi-mock mock status                      # Get mock endpoints status

# Start with mocks deactivated
fastapi-mock run my_mock.py --no-mocks        # Run service with inactive mocks
```

### 3. Advanced Usage with Error Codes

```python
from fastapi_mock_service import MockService
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

mock = MockService()

# Define error codes
API_ERRORS = {
    "validation": {"code": "API.01000", "message": "Validation error"},
    "not_found": {"code": "API.01001", "message": "Resource not found"},
    "server_error": {"code": "API.01003", "message": "Internal server error"},
}

class StandardResult(BaseModel):
    timestamp: str
    status: int
    code: str
    message: str

class UserResponse(BaseModel):
    result: StandardResult
    data: Optional[dict] = None

def make_result(success: bool = True, error_key: Optional[str] = None) -> StandardResult:
    dt = datetime.now(timezone.utc).isoformat()
    if success:
        return StandardResult(
            timestamp=dt, status=200, code="API.00000", message="OK"
        )
    else:
        error_info = API_ERRORS.get(error_key, API_ERRORS["server_error"])
        return StandardResult(
            timestamp=dt, status=200, 
            code=error_info["code"], message=error_info["message"]
        )

@mock.get("/api/v1/users/{user_id}")
def get_user_advanced(user_id: int):
    if user_id <= 0:
        return UserResponse(result=make_result(False, "validation"))
    
    if user_id > 1000:
        return UserResponse(result=make_result(False, "not_found"))
    
    # Success response
    user_data = {"id": user_id, "name": f"User {user_id}"}
    return UserResponse(result=make_result(True), data=user_data)

if __name__ == "__main__":
    mock.run()
```

## 🌐 Dashboard & Monitoring

Once your mock service is running, access:

- **📊 Dashboard**: `http://localhost:8000` - Interactive monitoring interface
- **📈 Metrics**: `http://localhost:8000/metrics` - Prometheus metrics endpoint
- **📚 API Docs**: `http://localhost:8000/docs` - Auto-generated API documentation

### Dashboard Features

- **Real-time Logs**: View incoming requests and responses
- **Metrics Visualization**: Charts for request counts, response times, and error rates
- **Test Management**: Start/stop load testing sessions
- **Endpoint Overview**: List of all registered mock endpoints
- **Test Results History**: Historical test results with detailed summaries
- **Independent Test Sessions**: Test sessions continue running even after closing the admin interface
- **Separate Mock Control**: Activate/deactivate mock endpoints independently of test sessions
- **Real-time Metrics**: Live updating charts and statistics

## 🧪 Load Testing

The service includes built-in load testing capabilities with independent test session management:

```python
# Your mock service automatically includes testing endpoints
# POST /api/start-test - Start a new test session
# POST /api/stop-test - Stop test and generate summary
# POST /api/reset-metrics - Reset all metrics
# GET /api/test-session-status - Get current test session status
# POST /api/stop-test-session - Stop test session by ID

# Example: Start test via HTTP
import httpx

# Start test in independent mode
response = httpx.post("http://localhost:8000/api/start-test",
                     json={"test_name": "Performance Test", "independent_mode": True})

# Get session ID from response
session_id = response.json()["test_session_id"]

# Your load testing tool hits the mock endpoints
# ... run your load tests ...

# Stop test and get results
results = httpx.post("http://localhost:8000/api/stop-test-session",
                    json={"test_session_id": session_id}).json()
print(results["summary"])

# Test continues even if admin interface is closed!
```

### CLI Test Management

For complete independence from the web interface, use the CLI commands:

```bash
# Start a test session
fastapi-mock test start --name "Load Test" --host localhost --port 8000

# Get test session status
fastapi-mock test status --host localhost --port 8000

# Stop the test session
fastapi-mock test stop --session-id <session_id> --host localhost --port 8000

# Force stop current test (no session ID needed)
fastapi-mock test stop --force --host localhost --port 8000

# Control mock endpoints independently
fastapi-mock mock activate --host localhost --port 8000
fastapi-mock mock deactivate --host localhost --port 8000
fastapi-mock mock status --host localhost --port 8000

# Start service with deactivated mocks
fastapi-mock run my_mock.py --no-mocks
```

## 📊 Metrics Collection

Automatic metrics collection includes:

- **Request Count**: Total requests per endpoint
- **Response Time**: Histogram of response times
- **Status Codes**: Distribution of response codes
- **Error Rates**: Success/failure ratios
- **Custom Result Codes**: Application-specific result codes

## 🛠️ API Reference

### MockService Class

```python
class MockService:
    def __init__(self, db_url: str = "sqlite://test_results.db"):
        """Initialize mock service with optional database URL"""
    
    def get(self, path: str = None, responses: list = None, tags: list = None):
        """GET endpoint decorator"""
    
    def post(self, path: str = None, responses: list = None, tags: list = None):
        """POST endpoint decorator"""
    
    def put(self, path: str = None, responses: list = None, tags: list = None):
        """PUT endpoint decorator"""
    
    def delete(self, path: str = None, responses: list = None, tags: list = None):
        """DELETE endpoint decorator"""
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the mock service"""
```

### Decorator Parameters

- **path**: URL path for the endpoint (defaults to function name)
- **responses**: List of possible responses for documentation
- **tags**: Tags for grouping endpoints in UI
- **validation_error_handler**: Custom validation error handler

## 📝 Examples

### Example 1: REST API Mock

```python
from fastapi_mock_service import MockService

mock = MockService()

@mock.get("/api/products/{product_id}")
def get_product(product_id: int, include_details: bool = False):
    product = {"id": product_id, "name": f"Product {product_id}"}
    if include_details:
        product["description"] = f"Description for product {product_id}"
    return product

@mock.get("/api/products")
def list_products(category: str = "all", limit: int = 10):
    return {
        "products": [{"id": i, "name": f"Product {i}"} for i in range(1, limit + 1)],
        "category": category,
        "total": limit
    }

mock.run()
```

### Example 2: With Custom Headers

```python
from fastapi_mock_service import MockService
from fastapi import Header

mock = MockService()

@mock.get("/api/secure/data")
def get_secure_data(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        return {"error": "Invalid authorization header"}
    
    return {"data": "sensitive information", "user": "authenticated"}

mock.run()
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitLab Issues](https://gitlab.com/eastden4ik/fastapimockserver/-/issues)
- **Email**: Sviridov.DS@bk.ru

## Acknowledgments
Built with:

- FastAPI - Modern, fast web framework
- Prometheus Client - Metrics collection
- Tortoise ORM - Async ORM for test results
- Chart.js - Interactive charts in dashboard


------------------------------------------
##### Made with ❤️ for the API development and testing community