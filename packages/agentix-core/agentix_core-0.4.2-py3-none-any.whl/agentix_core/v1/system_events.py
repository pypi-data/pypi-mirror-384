import aiohttp
import asyncio
import os
import logging
from threading import Thread
from typing import Optional, Dict, Any

logger = logging.getLogger("system.events")


class SystemEvents:
    """
    System Events logger - Static methods for fire-and-forget event logging.
    
    All methods return immediately and log events in the background.
    Perfect for system monitoring, telemetry, and application events.
    
    Usage:
        SystemEvents.info(JWT_TOKEN="your_token", message="Event message")
        SystemEvents.success(JWT_TOKEN=core.JWT_TOKEN, message="Success!")
    """

    @staticmethod
    async def __add_event(
        JWT_TOKEN: str,
        severity: str,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict | None:
        """
        Internal async method to add a system event to Core.
        Used by fire-and-forget background tasks.
        """
        try:
            if not JWT_TOKEN:
                logger.error("[SYSTEM-EVENTS] JWT_TOKEN is required and cannot be empty.")
                return None
                
            if not message:
                logger.error("[SYSTEM-EVENTS] message is required and cannot be empty.")
                return None

            if details is not None and not isinstance(details, dict):
                logger.error("[SYSTEM-EVENTS] details must be a dictionary.")
                return None

            if context is not None and not isinstance(context, dict):
                logger.error("[SYSTEM-EVENTS] context must be a dictionary.")
                return None

            # Get CORE_API from environment
            api_url = os.getenv("CORE_API")
            if not api_url:
                logger.error("[SYSTEM-EVENTS] CORE_API must be provided or set in environment variables.")
                return None

            url = f"{api_url.rstrip('/')}/v1/tools/system-events"
            headers = {
                "Authorization": f"Bearer {JWT_TOKEN}",
                "Referer": api_url,
                "Content-Type": "application/json"
            }

            # Build request body - only include non-None values
            event_data = {"severity": severity, "message": message}
            if service:
                event_data["service"] = service
            if details:
                event_data["details"] = details
            if context:
                event_data["context"] = context
            if tags:
                event_data["tags"] = tags

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=event_data, timeout=30) as response:
                    if response.status in [200, 201]:
                        result = await response.json() if "application/json" in response.headers.get("Content-Type", "") else {}
                        logger.info(f"✅ [SYSTEM-EVENTS] {severity.upper()} event logged: {message[:50]}...")
                        return result
                    else:
                        logger.error(f"❌ [SYSTEM-EVENTS] Failed to log {severity} event. Status: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ [SYSTEM-EVENTS] Error logging {severity} event: {str(e)}")
            return None

    @staticmethod
    def __fire_task(JWT_TOKEN: str, severity: str, message: str, service: str = None, 
                   details: dict = None, context: dict = None, tags: str = None):
        """Fire-and-forget task creation - never blocks."""
        try:
            # Try to create task in current event loop
            loop = asyncio.get_running_loop()
            loop.create_task(SystemEvents.__add_event(JWT_TOKEN, severity, message, service, details, context, tags))
        except RuntimeError:
            # No running loop - create thread with new event loop
            def run_in_thread():
                try:
                    asyncio.run(SystemEvents.__add_event(JWT_TOKEN, severity, message, service, details, context, tags))
                except Exception as e:
                    logger.error(f"❌ [SYSTEM-EVENTS] Background thread error: {e}")
            
            Thread(target=run_in_thread, daemon=True).start()

    # ========================================================================
    # PUBLIC API - Static methods, no object creation needed
    # ========================================================================
    
    @staticmethod
    def info(JWT_TOKEN: str, message: str, service: str = None, details: dict = None, 
             context: dict = None, tags: str = None) -> bool:
        """
        Log an informational event (fire-and-forget).
        Returns immediately, event is logged in background.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            bool: Always True (event is queued for background processing).

        Example:
            SystemEvents.info(
                JWT_TOKEN=core.JWT_TOKEN,
                message="Task processing started",
                service="task-processor",
                details={"task_key": "abc123"},
                tags="task,processing"
            )
        """
        SystemEvents.__fire_task(JWT_TOKEN, "info", message, service, details, context, tags)
        return True

    @staticmethod
    def success(JWT_TOKEN: str, message: str, service: str = None, details: dict = None, 
                context: dict = None, tags: str = None) -> bool:
        """
        Log a success event (fire-and-forget).
        Returns immediately, event is logged in background.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            bool: Always True (event is queued for background processing).

        Example:
            SystemEvents.success(
                JWT_TOKEN=core.JWT_TOKEN,
                message="Task completed successfully",
                details={"task_key": "abc123", "duration": 45.2},
                tags="task,success"
            )
        """
        SystemEvents.__fire_task(JWT_TOKEN, "success", message, service, details, context, tags)
        return True

    @staticmethod
    def warning(JWT_TOKEN: str, message: str, service: str = None, details: dict = None, 
                context: dict = None, tags: str = None) -> bool:
        """
        Log a warning event (fire-and-forget).
        Returns immediately, event is logged in background.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            bool: Always True (event is queued for background processing).

        Example:
            SystemEvents.warning(
                JWT_TOKEN=core.JWT_TOKEN,
                message="API rate limit approaching",
                details={"current_rate": 90, "limit": 100},
                tags="api,rate-limit"
            )
        """
        SystemEvents.__fire_task(JWT_TOKEN, "warning", message, service, details, context, tags)
        return True

    @staticmethod
    def error(JWT_TOKEN: str, message: str, service: str = None, details: dict = None, 
              context: dict = None, tags: str = None) -> bool:
        """
        Log an error event (fire-and-forget).
        Returns immediately, event is logged in background.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            bool: Always True (event is queued for background processing).

        Example:
            SystemEvents.error(
                JWT_TOKEN=core.JWT_TOKEN,
                message="Failed to process task",
                details={"task_key": "abc123", "error": "Connection timeout"},
                tags="task,error"
            )
        """
        SystemEvents.__fire_task(JWT_TOKEN, "error", message, service, details, context, tags)
        return True

    @staticmethod
    def critical(JWT_TOKEN: str, message: str, service: str = None, details: dict = None, 
                 context: dict = None, tags: str = None) -> bool:
        """
        Log a critical event (fire-and-forget).
        Returns immediately, event is logged in background.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            bool: Always True (event is queued for background processing).

        Example:
            SystemEvents.critical(
                JWT_TOKEN=core.JWT_TOKEN,
                message="Database connection lost",
                details={"database": "production", "last_connected": "2024-10-16T10:30:00Z"},
                tags="database,critical"
            )
        """
        SystemEvents.__fire_task(JWT_TOKEN, "critical", message, service, details, context, tags)
        return True