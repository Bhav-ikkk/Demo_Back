import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 3600):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()
            
            # Clean old entries
            self.clients = {
                ip: timestamps for ip, timestamps in self.clients.items()
                if any(t > current_time - self.period for t in timestamps)
            }
            
            # Check rate limit
            if client_ip in self.clients:
                self.clients[client_ip] = [
                    t for t in self.clients[client_ip] 
                    if t > current_time - self.period
                ]
                
                if len(self.clients[client_ip]) >= self.calls:
                    return Response(
                        content="Rate limit exceeded",
                        status_code=429,
                        headers={"Retry-After": str(self.period)}
                    )
            else:
                self.clients[client_ip] = []
            
            # Add current request
            self.clients[client_ip].append(current_time)
            
            return await call_next(request)
        except Exception as e:
            logger.error("Rate limit middleware error", error=str(e))
            return Response(
                content="Internal server error",
                status_code=500
            )
