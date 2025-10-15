"""
Base middleware module.
"""

from typing import Callable, Awaitable
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from mcp_proxy_adapter.core.logging import get_global_logger


class BaseMiddleware(BaseHTTPMiddleware):
    """
    Base class for all middleware.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Method that will be overridden in child classes.

        Args:
            request: Request.
            call_next: Next handler.

        Returns:
            Response.
        """
        middleware_name = self.__class__.__name__
        get_global_logger().info(f"🔍 STEP 1: {middleware_name}.dispatch START - {request.method} {request.url.path}")
        get_global_logger().info(f"🔍 STEP 1.1: {middleware_name} - Request headers: {dict(request.headers)}")
        get_global_logger().info(f"🔍 STEP 1.2: {middleware_name} - Request URL: {request.url}")
        get_global_logger().info(f"🔍 STEP 1.3: {middleware_name} - Request scope: {request.scope}")
        
        try:
            # Process request before calling the main handler
            get_global_logger().info(f"🔍 STEP 2: {middleware_name}.before_request START")
            await self.before_request(request)
            get_global_logger().info(f"🔍 STEP 3: {middleware_name}.before_request COMPLETED")

            # Call the next middleware or main handler
            get_global_logger().info(f"🔍 STEP 4: {middleware_name}.call_next START - About to call next middleware/endpoint")
            response = await call_next(request)
            get_global_logger().info(f"🔍 STEP 5: {middleware_name}.call_next COMPLETED - Status: {response.status_code}")
            get_global_logger().info(f"🔍 STEP 5.1: {middleware_name} - Response headers: {dict(response.headers)}")

            # Process response after calling the main handler
            get_global_logger().info(f"🔍 STEP 6: {middleware_name}.after_response START")
            response = await self.after_response(request, response)
            get_global_logger().info(f"🔍 STEP 7: {middleware_name}.after_response COMPLETED")

            get_global_logger().info(f"🔍 STEP 8: {middleware_name}.dispatch COMPLETED SUCCESSFULLY")
            return response
        except Exception as e:
            get_global_logger().error(f"❌ STEP ERROR: {middleware_name}.dispatch ERROR: {str(e)}", exc_info=True)
            # If an error occurred, call the error handler
            return await self.handle_error(request, e)

    async def before_request(self, request: Request) -> None:
        """
        Method for processing request before calling the main handler.

        Args:
            request: Request.
        """
        pass

    async def after_response(self, request: Request, response: Response) -> Response:
        """
        Method for processing response after calling the main handler.

        Args:
            request: Request.
            response: Response.

        Returns:
            Processed response.
        """
        return response

    async def handle_error(self, request: Request, exception: Exception) -> Response:
        """
        Method for handling errors that occurred in middleware.

        Args:
            request: Request.
            exception: Exception.

        Returns:
            Error response.
        """
        # By default, just pass the error further
        raise exception
