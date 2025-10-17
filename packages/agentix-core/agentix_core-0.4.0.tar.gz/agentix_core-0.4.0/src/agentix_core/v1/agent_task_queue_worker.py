import asyncio
import logging
import signal
import aio_pika
from aio_pika import IncomingMessage, Message
import json
from typing import Callable, Optional, Dict

logger = logging.getLogger(__name__)

DEFAULT_DELAY_MAPPING = {
    "30s": 30_000,
    "1m": 60_000,
    "5m": 300_000,
    "10m": 600_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
}

class AgentTaskQueueWorker:
    def __init__(
        self,
        queue_name: str,
        rabbitmq_url: str,
        process_task_callback: Callable[[IncomingMessage, asyncio.Semaphore, "AgentTaskQueueWorker"], asyncio.Future],
        prefetch_count: int = 5,
        max_concurrent_tasks: int = 5,
        enable_delayed_queue: bool = False,
        supported_delays: Optional[Dict[str, int]] = None
    ):
        if not queue_name:
            raise ValueError("queue_name must be provided")
        if not rabbitmq_url:
            raise ValueError("rabbitmq_url must be provided")
        if not process_task_callback:
            raise ValueError("process_task_callback must be provided")

        self.queue_name = queue_name
        self.rabbitmq_url = rabbitmq_url
        self.process_task_callback = process_task_callback
        self.prefetch_count = prefetch_count
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_delayed_queue = enable_delayed_queue

        self.supported_delays = supported_delays or DEFAULT_DELAY_MAPPING

        self.connection = None
        self.channel = None
        self.queue = None
        self.consumer_tag = None
        self.shutdown_event = asyncio.Event()

    def _setup_signal_handlers(self):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._shutdown(s)))

    async def _shutdown(self, signal_received):
        logger.info(f"🛑 Received shutdown signal: {signal_received}")
        try:
            if self.queue and self.consumer_tag:
                await self.queue.cancel(self.consumer_tag)
                logger.info("🚑 Consumer cancelled.")

            if self.channel and not self.channel.is_closed:
                await self.channel.close()
                logger.info("🚑 Channel closed.")

            if self.connection and not self.connection.is_closed:
                self.connection.reconnect_callbacks.clear()
                await self.connection.close()
                logger.info("🚑 Connection closed.")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        finally:
            self.shutdown_event.set()

    # ========================================================================================================
    # Start the worker and begin consuming messages from the queue
    # ========================================================================================================
    async def start(self):
        """
        Start the worker and begin consuming messages from the queue.
        This method connects to RabbitMQ, declares the queue, and starts consuming messages.
        It also sets up signal handlers for graceful shutdown.
        """
        logger.info(f"🚀 Starting Worker ... {self.queue_name}"
                    f"(Prefetch: {self.prefetch_count}, Max Concurrent: {self.max_concurrent_tasks})")

        while not self.shutdown_event.is_set():
            try:
                logger.info(f"🟢 Connecting to RabbitMQ: {self.rabbitmq_url}")
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url, heartbeat=30)

                self.connection.reconnect_callbacks.add(lambda _: logger.info("✅ Reconnected to RabbitMQ."))
                self.connection.close_callbacks.add(lambda _, exc: logger.warning(f"❌ Connection closed: {exc}"))

                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=self.prefetch_count)

                self.queue = await self.channel.declare_queue(self.queue_name, durable=True)
                semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

                self.consumer_tag = await self.queue.consume(
                    lambda msg: self.process_task_callback(msg, semaphore, self), no_ack=False
                )

                logger.info(f"✅ Consuming queue: {self.queue_name}")

                if self.enable_delayed_queue:
                    for label, ttl in self.supported_delays.items():
                        delayed_queue_name = f"{self.queue_name}_delayed_{label}"
                        await self.channel.declare_queue(
                            delayed_queue_name,
                            durable=True,
                            arguments={
                                "x-message-ttl": ttl,
                                "x-dead-letter-exchange": "",
                                "x-dead-letter-routing-key": self.queue_name
                            }
                        )
                        logger.info(f"📅 Declared delayed queue: {delayed_queue_name} with TTL {ttl}ms")

                self._setup_signal_handlers()
                await self.shutdown_event.wait()

            except Exception as e:
                if self.shutdown_event.is_set():
                    break
                logger.warning(f"🔴 Connection issue: {e}")
                logger.info("⏳ Retrying in 10 seconds...")
                await asyncio.sleep(10)

        logger.info("👋 AgentTaskQueueWorker exited cleanly.")

    # ========================================================================================================
    # Push a job to the delayed queue with a specified delay
    # ========================================================================================================
    async def push_delayed_task(self, job_data: dict, delay: str = "30s"):
        """
        Push a job to the delayed queue with a specified delay.
        :param job_data: The data for the job to be pushed, must be JSON-serializable.
        :param delay: The delay before the job is processed, must be one of the supported delays.
        :raises ValueError: If the delay is not supported or job_data is not JSON-serializable.
        :raises RuntimeError: If the worker is not connected to RabbitMQ or delayed queue is not enabled.
        """
        if not self.enable_delayed_queue:
            raise RuntimeError("Delayed queue is not enabled for this worker.")

        if delay not in self.supported_delays:
            raise ValueError(f"Unsupported delay value '{delay}'. Supported: {list(self.supported_delays.keys())}")

        if not self.connection or not self.channel:
            raise RuntimeError("Worker is not connected to RabbitMQ.")

        delayed_queue_name = f"{self.queue_name}_delayed_{delay}"

        try:
            body = json.dumps(job_data).encode()
        except (TypeError, ValueError) as e:
            raise ValueError("Invalid job_data: must be JSON-serializable") from e

        await self.channel.default_exchange.publish(
            Message(body=body),
            routing_key=delayed_queue_name
        )

        logger.info(f"✉️ Pushed job to delayed queue: {delayed_queue_name}")
