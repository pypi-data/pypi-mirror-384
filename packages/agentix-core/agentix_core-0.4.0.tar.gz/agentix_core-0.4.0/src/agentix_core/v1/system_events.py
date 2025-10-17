import aiohttp
import logging

logger = logging.getLogger("system.events")


class SystemEvents:
    """Handles system event logging to Core API."""

    def __init__(
        self,
        JWT_TOKEN: str,
        CORE_API: str,
        AGENT_NAME: str | None = None
    ):
        """
        Initialize SystemEvents handler with JWT token and Core API URL.

        Args:
            JWT_TOKEN (str): JWT token for authentication (required).
            CORE_API (str): Base URL of the Core API service (required).
            AGENT_NAME (str | None): The agent's username (optional, used for auto-population).

        Raises:
            ValueError: If JWT_TOKEN or CORE_API is missing or empty.
        """
        if not JWT_TOKEN:
            raise ValueError("[SYSTEM-EVENTS] JWT_TOKEN is required and cannot be empty.")
        
        if not CORE_API:
            raise ValueError("[SYSTEM-EVENTS] CORE_API is required and cannot be empty.")

        self.JWT_TOKEN = JWT_TOKEN
        self.CORE_API = CORE_API.rstrip("/")
        self.AGENT_NAME = AGENT_NAME

    async def _add_event(
        self,
        severity: str,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Internal method to add a system event to Core.

        Args:
            severity (str): Event severity level (info, success, warning, error, critical).
            message (str): Event message or description (required).
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization (comma-separated string).

        Returns:
            dict: The created event data from the API response.

        Raises:
            ValueError: If message is empty or parameters are invalid.
            RuntimeError: If the API request fails.
        """
        if not message:
            raise ValueError("[SYSTEM-EVENTS] message is required and cannot be empty.")

        if details is not None and not isinstance(details, dict):
            raise ValueError("[SYSTEM-EVENTS] details must be a dictionary.")

        if context is not None and not isinstance(context, dict):
            raise ValueError("[SYSTEM-EVENTS] context must be a dictionary.")

        # Auto-populate service from AGENT_NAME if not provided
        if not service and self.AGENT_NAME:
            service = self.AGENT_NAME

        # Auto-add agent info to context if not already present
        if context is None:
            context = {}
        
        if self.AGENT_NAME and "agent_name" not in context:
            context["agent_name"] = self.AGENT_NAME

        url = f"{self.CORE_API}/v1/tools/system-events"
        headers = {
            "Authorization": f"Bearer {self.JWT_TOKEN}",
            "Referer": self.CORE_API,
            "Content-Type": "application/json"
        }

        # Build request body - only include non-None values
        event_data = {
            "severity": severity,
            "message": message
        }

        if service:
            event_data["service"] = service
        if details:
            event_data["details"] = details
        if context:
            event_data["context"] = context
        if tags:
            event_data["tags"] = tags

        try:
            logger.info(f"📝 [SYSTEM-EVENTS] Adding {severity.upper()} event: {message[:50]}...")
            logger.debug(f"📦 [SYSTEM-EVENTS] Request payload: {event_data}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=event_data) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None

                    if response.status in [200, 201]:
                        return response_json
                    else:
                        logger.error(f"❌ [SYSTEM-EVENTS] Failed to create event. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [SYSTEM-EVENTS] Failed to create event. HTTP Status: {response.status} - {response_json}")

        except Exception as e:
            logger.error(f"❌ [SYSTEM-EVENTS] Exception while creating event: {e}")
            raise RuntimeError(f"❌ [SYSTEM-EVENTS] Exception while creating event: {e}")

    async def info(
        self,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Log an informational system event.

        Args:
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            dict: The created event data from the API response.

        Example:
            await events.info(
                message="Task processing started",
                service="task-processor",
                details={"task_key": "abc123"},
                tags="task,processing"
            )
        """
        return await self._add_event(
            severity="info",
            message=message,
            service=service,
            details=details,
            context=context,
            tags=tags
        )

    async def success(
        self,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Log a success system event.

        Args:
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            dict: The created event data from the API response.

        Example:
            await events.success(
                message="Task completed successfully",
                details={"task_key": "abc123", "duration": 45.2},
                tags="task,success"
            )
        """
        return await self._add_event(
            severity="success",
            message=message,
            service=service,
            details=details,
            context=context,
            tags=tags
        )

    async def warning(
        self,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Log a warning system event.

        Args:
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            dict: The created event data from the API response.

        Example:
            await events.warning(
                message="API rate limit approaching",
                details={"current_rate": 90, "limit": 100},
                tags="api,rate-limit"
            )
        """
        return await self._add_event(
            severity="warning",
            message=message,
            service=service,
            details=details,
            context=context,
            tags=tags
        )

    async def error(
        self,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Log an error system event.

        Args:
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            dict: The created event data from the API response.

        Example:
            await events.error(
                message="Failed to process task",
                details={"task_key": "abc123", "error": "Connection timeout"},
                tags="task,error"
            )
        """
        return await self._add_event(
            severity="error",
            message=message,
            service=service,
            details=details,
            context=context,
            tags=tags
        )

    async def critical(
        self,
        message: str,
        service: str | None = None,
        details: dict | None = None,
        context: dict | None = None,
        tags: str | None = None
    ) -> dict:
        """
        Log a critical system event.

        Args:
            message (str): Event message or description.
            service (str | None): Service or component that generated the event.
            details (dict | None): Additional event details as JSON object.
            context (dict | None): Event context information as JSON object.
            tags (str | None): Event tags for categorization.

        Returns:
            dict: The created event data from the API response.

        Example:
            await events.critical(
                message="Database connection lost",
                details={"database": "production", "last_connected": "2024-10-16T10:30:00Z"},
                tags="database,critical"
            )
        """
        return await self._add_event(
            severity="critical",
            message=message,
            service=service,
            details=details,
            context=context,
            tags=tags
        )
