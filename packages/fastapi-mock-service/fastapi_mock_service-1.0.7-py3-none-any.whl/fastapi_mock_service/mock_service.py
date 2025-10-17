import asyncio
import inspect
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Callable
from pathlib import Path

try:
    from importlib.resources import files  # Python 3.9+
except ImportError:
    from importlib_resources import files  # backport for Python 3.8

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from pydantic import BaseModel
from starlette.responses import Response
from tortoise import Tortoise, fields
from tortoise.exceptions import ConfigurationError, DoesNotExist
from tortoise.models import Model


# Database Models
class TestResult(Model):
    id = fields.IntField(pk=True)
    test_name = fields.CharField(max_length=255)
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField(null=True)
    total_requests = fields.IntField(default=0)
    successful_requests = fields.IntField(default=0)
    failed_requests = fields.IntField(default=0)
    avg_response_time = fields.FloatField(default=0.0)
    summary = fields.TextField(null=True)

    class Meta:
        table = "test_results"


# Prometheus Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
test_metrics = Counter('test_requests_total', 'Test requests', ['endpoint', 'status'])
test_code_metrics = Counter('test_code_total', 'Test requests by result code', ['endpoint', 'code'])
test_endpoint_metrics = Counter('test_endpoint_total', 'Test requests by endpoint', ['endpoint'])

# Глобальное хранилище логов для UI
ui_logs = []
MAX_UI_LOGS = 100

# Глобальное хранилище endpoint'ов для UI
mock_endpoints = []

# Глобальное состояние активности моков
mocks_active = False
# Глобальное состояние тестирования (независимо от админки)
test_session_active = False
test_session_id = None

def add_ui_log(message: str, log_type: str = "info"):
    """Добавить лог для отображения в UI"""
    global ui_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    ui_logs.append({
        "timestamp": timestamp,
        "message": message,
        "type": log_type
    })

    # Ограничиваем количество логов
    if len(ui_logs) > MAX_UI_LOGS:
        ui_logs = ui_logs[-MAX_UI_LOGS:]


def register_endpoint(method: str, path: str, service: str, handler: Callable, responses: list = None,
                      tags: list = None):
    """Зарегистрировать endpoint для отображения в UI"""
    # Проверяем, есть ли уже такой endpoint
    for endpoint in mock_endpoints:
        if endpoint["method"] == method and endpoint["path"] == path:
            # Обновляем информацию о сервисе и ответах
            endpoint["service"] = service
            endpoint["responses"] = responses or []
            endpoint["tags"] = tags or []
            return

    # Добавляем новый endpoint
    mock_endpoints.append({
        "method": method,
        "path": path,
        "service": service,
        "handler": handler.__name__,
        "responses": responses or [],
        "tags": tags or []
    })


# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Tortoise.init(
        db_url="sqlite://test_results.db",
        modules={"models": ["fastapi_mock_service.mock_service"]}
    )
    await Tortoise.generate_schemas()
    logging.info("Application started")
    yield
    # Shutdown
    await Tortoise.close_connections()
    logging.info("Application shutdown")


class MockService:
    def __init__(self, db_url: str = "sqlite://test_results.db"):
        self.db_url = db_url
        self.current_test_start = None
        self.current_test_name = "Load Test"
        self.app = FastAPI(
            title="FastAPI Mock Service",
            version="1.0.0",
            lifespan=lifespan
        )

        # CORS configuration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Может быть ограничено на нужные домены
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup templates
        try:
            # Пытаемся найти templates в установленном пакете
            template_dir = Path(files('fastapi_mock_service').joinpath('templates'))
        except (ImportError, FileNotFoundError):
            # Fallback для development режима
            template_dir = Path(__file__).parent / 'templates'

        self.templates = Jinja2Templates(directory=template_dir)

        # Инициализируем endpoint'ы
        self._setup_routes()

    def _setup_routes(self):
        """Настройка всех endpoint'ов"""
        # Добавляем middleware для сбора метрик
        self.app.middleware("http")(self.metrics_middleware)

        # Основные endpoint'ы
        self.app.get("/metrics")(self.metrics)
        self.app.get("/", response_class=HTMLResponse)(self.dashboard)
        self.app.post("/api/start-test")(self.start_test)
        self.app.post("/api/stop-test")(self.stop_test)
        self.app.post("/api/reset-metrics")(self.reset_metrics)
        self.app.get("/api/ui-logs")(self.get_ui_logs)
        self.app.post("/api/clear-ui-logs")(self.clear_ui_logs)
        self.app.get("/api/test-results")(self.get_test_results)
        self.app.get("/api/endpoints")(self.get_endpoints)
        self.app.get("/api/mock-status")(self.get_mock_status)
        self.app.post("/api/activate-mocks")(self.activate_mocks)
        self.app.post("/api/deactivate-mocks")(self.deactivate_mocks)
        self.app.get("/api/test-session-status")(self.get_test_session_status)
        self.app.post("/api/stop-test-session")(self.stop_test_session)

    async def metrics_middleware(self, request: Request, call_next):
        start_time = datetime.now()

        # Логируем входящий mock запрос
        endpoint = request.url.path
        method = request.method

        # Проверяем, является ли endpoint частью mock сервиса
        # Для этого используем более общий подход - считаем mock endpoint'ами
        # все запросы, кроме системных
        system_endpoints = ["/", "/metrics", "/api/start-test", "/api/stop-test",
                            "/api/reset-metrics", "/api/test-results", "/api/ui-logs",
                            "/api/clear-ui-logs", "/api/endpoints", "/api/mock-status",
                            "/api/activate-mocks", "/api/deactivate-mocks",
                            "/api/test-session-status", "/api/stop-test-session",
                            "/docs", "/redoc", "/openapi.json"]

        is_system_endpoint = endpoint in system_endpoints
        is_mock_endpoint = not is_system_endpoint and method in ["GET", "POST", "PUT", "DELETE", "PATCH"]

        if is_mock_endpoint and not mocks_active:
            logging.debug(f"Mock endpoint {endpoint} is not active")
            return JSONResponse(
                status_code=503,
                content={
                    "result": {
                        "timestamp": datetime.now().isoformat(),
                        "status": 503,
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Mock endpoints are not active. Start a test to activate them."
                    },
                    "data": None
                }
            )

        if is_mock_endpoint:
            # Логируем входящий запрос
            query_params = str(request.query_params) if request.query_params else ""
            headers_info = f"Headers: {dict(request.headers)}" if request.headers else ""

            add_ui_log(f"🔵 ВХОДЯЩИЙ: {method} {endpoint}", "request")
            if query_params:
                add_ui_log(f"   Параметры: {query_params}", "request")

            # Получаем body для POST/PUT/PATCH запросов
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        body_str = body.decode('utf-8')[:200] + ("..." if len(body) > 200 else "")
                        add_ui_log(f"   Body: {body_str}", "request")
                except Exception:
                    pass

        response = await call_next(request)

        duration = (datetime.now() - start_time).total_seconds()
        status = response.status_code

        if is_mock_endpoint:
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            # Логируем ответ
            status_emoji = "🟢" if status < 400 else "🔴"
            add_ui_log(f"{status_emoji} ОТВЕТ: {status} - {duration:.3f}s",
                       "response" if status < 400 else "error")

            logging.info(f"MOCK: {method} {endpoint} - {status} - {duration:.3f}s")
        else:
            logging.debug(f"SYSTEM: {method} {endpoint} - {status} - {duration:.3f}s")

        return response

    async def metrics(self):
        """Prometheus metrics endpoint"""
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    async def dashboard(self, request: Request):
        """Main dashboard UI"""
        try:
            test_results = await TestResult.all().order_by('-id').limit(10)
        except Exception as e:
            logging.error(f"Error fetching test results: {e}")
            test_results = []

        return self.templates.TemplateResponse("dashboard.html", {
            "request": request,
            "test_results": test_results,
            "current_test_name": self.current_test_name,
            "endpoints": mock_endpoints,
            "mocks_active": mocks_active
        })

    async def start_test(self, request: Request):
        """Start new test session"""
        logging.info("Start test endpoint called")

        try:
            body = await request.json()
            test_name = body.get('test_name', 'Load Test')
            # Добавляем опцию для независимого режима
            independent_mode = body.get('independent_mode', False)
            logging.info(f"Received test name: {test_name}, independent_mode: {independent_mode}")
        except Exception as e:
            logging.warning(f"Error parsing request body: {e}, using default test name")
            test_name = "Load Test"
            independent_mode = False

        self.current_test_start = datetime.now()
        self.current_test_name = test_name

        # Генерируем уникальный ID для сессии тестирования
        import uuid
        global test_session_id, test_session_active, mocks_active
        
        test_session_id = str(uuid.uuid4())
        test_session_active = True

        # Clear metrics and UI logs
        request_count.clear()
        request_duration.clear()
        test_metrics.clear()
        test_code_metrics.clear()  # Очищаем метрики по кодам
        test_endpoint_metrics.clear()  # Очищаем метрики по endpoint'ам
        global ui_logs
        ui_logs = []  # Очищаем UI логи
        mocks_active = True  # Активируем моки

        add_ui_log("=== ТЕСТ ЗАПУЩЕН ===", "system")
        add_ui_log(f"ID сессии: {test_session_id}", "system")
        add_ui_log(f"Название: {test_name}", "system")
        add_ui_log(f"Режим: {'Независимый' if independent_mode else 'Обычный'}", "system")
        add_ui_log("Метрики и логи очищены", "system")
        add_ui_log("Mock endpoint'ы активированы", "system")
        add_ui_log("Ожидание mock запросов...", "system")

        logging.info(f"Test started: {test_name} (ID: {test_session_id})")
        logging.info(f"Test session active: {test_session_active}")
        logging.info(f"Mocks activated: {mocks_active}")
        
        return {
            "status": "Test started",
            "test_name": test_name,
            "test_session_id": test_session_id,
            "mocks_active": mocks_active,
            "independent_mode": independent_mode
        }

    async def stop_test(self, request: Request = None):
        """Stop test and generate summary"""
        logging.info("Stop test endpoint called")

        if not self.current_test_start:
            logging.warning("No active test to stop")
            raise HTTPException(status_code=400, detail="No active test")

        end_time = datetime.now()
        duration = (end_time - self.current_test_start).total_seconds()

        # Деактивируем моки и сессию тестирования
        global mocks_active, test_session_active, test_session_id
        
        # Проверяем, если запрос содержит ID сессии
        session_id_from_request = None
        if request:
            try:
                body = await request.json()
                session_id_from_request = body.get('test_session_id')
            except Exception:
                pass  # Игнорируем ошибки парсинга
        
        # Если ID сессии не указан или совпадает с текущим, останавливаем тест
        if session_id_from_request is None or session_id_from_request == test_session_id:
            mocks_active = False
            test_session_active = False
            current_session_id = test_session_id
            test_session_id = None
        else:
            # Если ID не совпадает, возвращаем ошибку
            logging.warning(f"Session ID mismatch: expected {test_session_id}, got {session_id_from_request}")
            raise HTTPException(status_code=400, detail="Session ID mismatch")

        # Calculate metrics
        try:
            # Получаем только метрики для mock endpoints
            mock_request_samples = []
            all_samples = request_count.collect()[0].samples

            # Filter out system endpoints
            system_endpoints = ["/", "/metrics", "/api/start-test", "/api/stop-test",
                                "/api/reset-metrics", "/api/test-results", "/api/ui-logs",
                                "/api/clear-ui-logs", "/api/endpoints", "/api/mock-status",
                                "/api/activate-mocks", "/api/deactivate-mocks",
                                "/api/test-session-status", "/api/stop-test-session",
                                "/docs", "/redoc", "/openapi.json"]

            for sample in all_samples:
                endpoint_label = sample.labels.get('endpoint', '')
                if endpoint_label not in system_endpoints:
                    mock_request_samples.append(sample)

            total_requests = sum(sample.value for sample in mock_request_samples)

            # Detalization by code for test_code_metrics
            code_counts = {}
            code_metrics_samples = test_code_metrics.collect()[0].samples
            for sample in code_metrics_samples:
                code = sample.labels.get('code', 'unknown')
                value = int(sample.value)
                if value > 0:
                    code_counts.setdefault(code, 0)
                    code_counts[code] += value

            codes_summary = '\n'.join([f'- {code}: {count} ({count / total_requests * 100:.2f}%)' for code, count in
                                       code_counts.items()]) if total_requests else ''

            # Optionally for backward compatibility, keep successful_requests/failed_requests
            # but now we treat "success" as code==CUSTATMC.00000 or PROFICMP.00000 (OK codes)
            ok_codes = {'CUSTATMC.00000', 'PROFICMP.00000'}
            successful_requests = sum(count for code, count in code_counts.items() if code in ok_codes)
            failed_requests = total_requests - successful_requests

            # Get average response time for mock endpoints only
            mock_duration_samples = []
            all_duration_samples = request_duration.collect()[0].samples

            for sample in all_duration_samples:
                endpoint_label = sample.labels.get('endpoint', '')
                if endpoint_label not in system_endpoints:
                    mock_duration_samples.append(sample)

            total_time = sum(s.value for s in mock_duration_samples if s.name.endswith('_sum'))
            avg_response_time = total_time / total_requests if total_requests > 0 else 0

            summary = (f"Test Summary (Mock Endpoints Only):\n"
                       f"- Duration: {duration:.2f} seconds\n"
                       f"- Total Mock Requests: {int(total_requests)}\n"
                       f"- Code distribution by result:\n{codes_summary}\n"
                       f"- Avg Response Time: {avg_response_time:.3f}s")

            # Save to database
            test_result = await TestResult.create(
                test_name=self.current_test_name,
                start_time=self.current_test_start,
                end_time=end_time,
                total_requests=int(total_requests),
                successful_requests=int(successful_requests),
                failed_requests=int(failed_requests),
                avg_response_time=avg_response_time,
                summary=summary
            )

            logging.info(f"Test completed: {self.current_test_name}")
            logging.info(summary)

            self.current_test_start = None
            logging.info(f"Test session completed: {current_session_id}")
            logging.info(f"Test session active: {test_session_active}")
            logging.info(f"Mocks deactivated: {mocks_active}")
            return {
                "status": "Test completed",
                "summary": summary,
                "test_id": test_result.id,
                "test_session_id": current_session_id,
                "mocks_active": mocks_active
            }

        except Exception as e:
            logging.error(f"Error calculating metrics: {e}")
            self.current_test_start = None
            mocks_active = False
            test_session_active = False
            current_session_id = test_session_id
            test_session_id = None
            return {
                "status": "Test completed with errors",
                "error": str(e),
                "test_session_id": current_session_id,
                "mocks_active": mocks_active
            }

    async def reset_metrics(self):
        """Reset all metrics"""
        logging.info("Reset metrics endpoint called")

        request_count.clear()
        request_duration.clear()
        test_metrics.clear()
        test_code_metrics.clear()  # Очищаем метрики по кодам
        test_endpoint_metrics.clear()  # Очищаем метрики по endpoint'ам
        global ui_logs, mocks_active
        ui_logs = []  # Очищаем UI логи
        mocks_active = False  # Деактивируем моки при сбросе

        add_ui_log("=== МЕТРИКИ СБРОШЕНЫ ===", "system")
        add_ui_log("Все счетчики обнулены", "system")
        add_ui_log("Mock endpoint'ы деактивированы", "system")

        logging.info("Metrics reset")
        return {"status": "Metrics reset", "mocks_active": mocks_active}

    async def get_ui_logs(self):
        """Get UI logs for dashboard"""
        return {"logs": ui_logs}

    async def clear_ui_logs(self):
        """Clear UI logs"""
        global ui_logs
        ui_logs = []
        logging.info("UI logs cleared")
        return {"status": "UI logs cleared"}

    async def get_test_results(self):
        """Get all test results"""
        try:
            results = await TestResult.all().order_by('-id')
            return [
                {
                    "id": r.id,
                    "test_name": r.test_name,
                    "start_time": r.start_time.isoformat(),
                    "end_time": r.end_time.isoformat() if r.end_time else None,
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "avg_response_time": r.avg_response_time,
                    "summary": r.summary
                } for r in results
            ]
        except DoesNotExist:
            logging.error("No test results found")
            raise HTTPException(status_code=404, detail="No test results found")
        except ConfigurationError as ce:
            logging.error(f"Database configuration error: {ce}")
            raise HTTPException(status_code=500, detail=f"Database configuration error: {str(ce)}")
        except Exception as e:
            logging.error(f"Error fetching test results: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    async def get_endpoints(self):
        """Get all registered mock endpoints"""
        return {"endpoints": mock_endpoints}

    async def get_mock_status(self):
        """Get mock endpoints status"""
        global test_session_active
        return {
            "mocks_active": mocks_active,
            "endpoints_count": len(mock_endpoints),
            "test_session_active": test_session_active
        }
    
    async def activate_mocks(self, request: Request):
        """Activate mock endpoints independently of test session"""
        global mocks_active
        
        try:
            body = await request.json()
            reason = body.get('reason', 'Manual activation')
        except Exception:
            reason = 'Manual activation'
        
        mocks_active = True
        
        add_ui_log("=== МОКИ АКТИВИРОВАНЫ ===", "system")
        add_ui_log(f"Причина: {reason}", "system")
        add_ui_log("Mock endpoint'ы готовы к приему запросов", "system")
        
        logging.info(f"Mocks activated: {reason}")
        return {
            "status": "Mocks activated",
            "mocks_active": mocks_active,
            "reason": reason
        }
    
    async def deactivate_mocks(self, request: Request):
        """Deactivate mock endpoints independently of test session"""
        global mocks_active
        
        try:
            body = await request.json()
            reason = body.get('reason', 'Manual deactivation')
        except Exception:
            reason = 'Manual deactivation'
        
        mocks_active = False
        
        add_ui_log("=== МОКИ ДЕАКТИВИРОВАНЫ ===", "system")
        add_ui_log(f"Причина: {reason}", "system")
        add_ui_log("Mock endpoint'ы больше не принимают запросы", "system")
        
        logging.info(f"Mocks deactivated: {reason}")
        return {
            "status": "Mocks deactivated",
            "mocks_active": mocks_active,
            "reason": reason
        }
    
    async def get_test_session_status(self):
        """Get current test session status"""
        global test_session_active, test_session_id, mocks_active
        
        return {
            "test_session_active": test_session_active,
            "test_session_id": test_session_id,
            "mocks_active": mocks_active,
            "current_test_name": self.current_test_name if test_session_active else None,
            "test_start_time": self.current_test_start.isoformat() if self.current_test_start else None
        }
    
    async def stop_test_session(self, request: Request):
        """Stop test session by ID (independent of admin interface)"""
        logging.info("Stop test session endpoint called")
        
        try:
            body = await request.json()
            session_id = body.get('test_session_id')
            force_stop = body.get('force_stop', False)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")
        
        global test_session_active, test_session_id
        
        if not test_session_active:
            logging.warning("No active test session to stop")
            raise HTTPException(status_code=400, detail="No active test session")
        
        if not force_stop and session_id != test_session_id:
            logging.warning(f"Session ID mismatch: expected {test_session_id}, got {session_id}")
            raise HTTPException(status_code=400, detail="Session ID mismatch")
        
        # Вызываем обычный stop_test, но с специальным флагом
        return await self.stop_test(request)

    def _create_mock_endpoint(self, method: str, path: str = None, responses: list = None, tags: list = None,
                              validation_error_handler: Callable = None):
        """
        Создает декоратор для mock endpoint'а в стиле FastAPI

        Args:
            method: HTTP метод ("GET", "POST", "PUT", "DELETE", "PATCH")
            path: Путь endpoint'а
            responses: Список возможных ответов для отображения в UI
            tags: Теги для группировки endpoint'ов в UI
            validation_error_handler: Функция для обработки ошибок валидации
        """
        def decorator(handler: Callable):
            # Получаем имя функции для service
            service_name = handler.__name__

            # Если path не указан, используем имя функции
            endpoint_path = path or f"/{service_name}"

            # Используем переданные responses или пустой список
            endpoint_responses = responses or []

            # Регистрируем endpoint для отображения в UI
            register_endpoint(method, endpoint_path, service_name, handler, endpoint_responses, tags)

            # Получаем сигнатуру функции для правильной передачи параметров
            sig = inspect.signature(handler)

            # Создаем обертку для handler'а, которая будет собирать метрики
            async def wrapped_handler(request: Request):
                try:
                    # Создаем словарь параметров для передачи в handler
                    kwargs = {}

                    # Проверяем обязательные параметры и добавляем query параметры для GET запросов
                    if method.upper() == "GET" and request.query_params:
                        for key, value in request.query_params.items():
                            if key in sig.parameters:
                                kwargs[key] = value

                    # Добавляем path параметры
                    if request.path_params:
                        for key, value in request.path_params.items():
                            if key in sig.parameters:
                                # Пытаемся преобразовать тип если необходимо
                                param = sig.parameters[key]
                                if param.annotation and param.annotation != inspect.Parameter.empty:
                                    try:
                                        kwargs[key] = param.annotation(value)
                                    except (ValueError, TypeError):
                                        kwargs[key] = value
                                else:
                                    kwargs[key] = value

                    # Добавляем заголовки если они нужны функции
                    for param_name, param in sig.parameters.items():
                        if hasattr(param.default, 'alias'):  # Для Header параметров
                            header_name = param.default.alias
                            if header_name in request.headers:
                                kwargs[param_name] = request.headers[header_name]
                            elif param.default.default is not ...:  # Есть значение по умолчанию
                                kwargs[param_name] = param.default.default

                    # Для POST/PUT/PATCH запросов добавляем body
                    if method.upper() in ["POST", "PUT", "PATCH"]:
                        try:
                            body = await request.body()
                            if body:
                                # Пытаемся распарсить JSON
                                try:
                                    json_body = json.loads(body.decode('utf-8'))
                                    # Ищем параметр для body данных
                                    for param_name, param in sig.parameters.items():
                                        if (param.annotation and
                                                hasattr(param.annotation, '__bases__') and
                                                BaseModel in param.annotation.__bases__):
                                            kwargs[param_name] = param.annotation(**json_body)
                                            break
                                    else:
                                        # Если не нашли подходящий параметр, добавляем как request
                                        if 'request' in sig.parameters:
                                            kwargs['request'] = json_body
                                except json.JSONDecodeError:
                                    # Если не JSON, передаем как текст
                                    if 'request' in sig.parameters:
                                        kwargs['request'] = body.decode('utf-8')
                        except Exception:
                            pass

                    # Проверяем обязательные параметры
                    missing_required = []
                    for param_name, param in sig.parameters.items():
                        if (param.default is inspect.Parameter.empty and
                                param_name not in kwargs and
                                not hasattr(param.default, 'alias')):  # Не Header параметр
                            missing_required.append(param_name)

                    # Если есть отсутствующие обязательные параметры, вызываем обработчик валидации
                    if missing_required:
                        if validation_error_handler:
                            return validation_error_handler(missing_required, endpoint_path, service_name)
                        else:
                            # Возвращаем базовую ошибку валидации без специфичных кодов
                            from datetime import datetime, timezone
                            return {
                                "result": {
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "status": 200,
                                    "code": "VALIDATION_ERROR",
                                    "message": f"Missing required parameters: {', '.join(missing_required)}"
                                },
                                "data": None
                            }

                    # Определяем, является ли handler корутиной
                    if asyncio.iscoroutinefunction(handler):
                        response = await handler(**kwargs)
                    else:
                        response = handler(**kwargs)

                    # Собираем метрики для теста
                    test_metrics.labels(endpoint=service_name, status="success").inc()
                    test_endpoint_metrics.labels(endpoint=endpoint_path).inc()

                    # Если response содержит код результата, регистрируем его
                    if hasattr(response, 'result') and hasattr(response.result, 'code'):
                        test_code_metrics.labels(endpoint=service_name, code=response.result.code).inc()

                    return response
                except Exception as e:
                    # В случае ошибки тоже собираем метрики
                    test_metrics.labels(endpoint=service_name, status="error").inc()
                    logging.error(f"Error in mock endpoint {endpoint_path}: {e}")
                    raise e

            # Регистрируем endpoint в зависимости от метода
            if method.upper() == "GET":
                self.app.get(endpoint_path)(wrapped_handler)
            elif method.upper() == "POST":
                self.app.post(endpoint_path)(wrapped_handler)
            elif method.upper() == "PUT":
                self.app.put(endpoint_path)(wrapped_handler)
            elif method.upper() == "DELETE":
                self.app.delete(endpoint_path)(wrapped_handler)
            elif method.upper() == "PATCH":
                self.app.patch(endpoint_path)(wrapped_handler)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return handler

        return decorator

    def get(self, path: str = None, responses: list = None, tags: list = None,
            validation_error_handler: Callable = None):
        """GET декоратор в стиле FastAPI"""
        return self._create_mock_endpoint("GET", path, responses, tags, validation_error_handler)

    def post(self, path: str = None, responses: list = None, tags: list = None,
             validation_error_handler: Callable = None):
        """POST декоратор в стиле FastAPI"""
        return self._create_mock_endpoint("POST", path, responses, tags, validation_error_handler)

    def put(self, path: str = None, responses: list = None, tags: list = None,
            validation_error_handler: Callable = None):
        """PUT декоратор в стиле FastAPI"""
        return self._create_mock_endpoint("PUT", path, responses, tags, validation_error_handler)

    def delete(self, path: str = None, responses: list = None, tags: list = None,
               validation_error_handler: Callable = None):
        """DELETE декоратор в стиле FastAPI"""
        return self._create_mock_endpoint("DELETE", path, responses, tags, validation_error_handler)

    def patch(self, path: str = None, responses: list = None, tags: list = None,
              validation_error_handler: Callable = None):
        """PATCH декоратор в стиле FastAPI"""
        return self._create_mock_endpoint("PATCH", path, responses, tags, validation_error_handler)

    def add_mock_endpoint(self, method: str, path: str, service: str, responses: list = None, tags: list = None):
        """
        Добавление mock endpoint'а к приложению с автоматическим логированием и метриками
        (Обратная совместимость)

        Args:
            method: HTTP метод ("GET", "POST", "PUT", "DELETE", "PATCH")
            path: Путь endpoint'а
            service: Название сервиса для логирования
            responses: Список возможных ответов для отображения в UI
            tags: Теги для группировки endpoint'ов в UI
        """
        def decorator(handler: Callable):
            # Регистрируем endpoint для отображения в UI
            register_endpoint(method, path, service, handler, responses, tags)
            return self._create_mock_endpoint(method, path, responses, tags)(handler)
        return decorator

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Запуск приложения"""
        uvicorn.run(self.app, host=host, port=port, **kwargs)
