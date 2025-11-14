"""
Middleware de logging para requisições HTTP
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logar todas as requisições HTTP
    """

    async def dispatch(self, request: Request, call_next):
        """
        Processa a requisição e loga informações relevantes

        Args:
            request: Requisição HTTP
            call_next: Próximo middleware ou rota

        Returns:
            Response: Resposta HTTP
        """
        start_time = time.time()

        # Informações da requisição
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # Log da requisição
        logger.info(f"Request: {method} {url} - Client: {client_host}")

        # Processa a requisição
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log da resposta
            logger.info(
                f"Response: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            # Adiciona header com tempo de processamento
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {method} {url} - "
                f"Exception: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise
