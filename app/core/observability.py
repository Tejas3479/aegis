import time
import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Centralized Enterprise Logger
logger = logging.getLogger("aegis_enterprise")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
)

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise telemetry middleware for request tracing, latency monitoring, and audit logging.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Inject request_id into logger context
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        logging.setLogRecordFactory(record_factory)

        start_time = time.time()
        
        # Log incoming request
        logger.info(f"Incoming {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time-MS"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            logger.info(f"Completed {request.method} {request.url.path} in {process_time:.2f}ms with status {response.status_code}")
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Failed {request.method} {request.url.path} after {process_time:.2f}ms - Error: {str(e)}")
            raise e
        finally:
            # Restore factory to avoid leaks if needed (simplified for demonstration)
            logging.setLogRecordFactory(old_factory)

def get_enterprise_logger(name: str):
    return logging.getLogger(f"aegis_enterprise.{name}")
