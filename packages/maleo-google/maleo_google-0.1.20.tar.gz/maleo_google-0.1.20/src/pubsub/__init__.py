import asyncio
import inspect
import threading
import traceback
from abc import ABC, abstractmethod
from copy import deepcopy
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import FlowControl
from typing import Any, Coroutine, Dict, Generic, Sequence
from maleo.logging.config import LogConfig
from maleo.schemas.application import OptApplicationContext
from maleo.schemas.resource import AggregateField, ResourceIdentifier
from maleo.types.misc import OptPathOrStr
from maleo.utils.exception import extract_details
from ..base import GOOGLE_RESOURCE, GoogleClientManager
from ..types import OptionalCredentials
from .config import PubSubConfig
from .config.publisher import PublisherConfigT
from .config.subscription import SubscriptionsConfigT
from .handlers import SubscriptionHandler
from .types import R, MessageController


PUBSUB_RESOURCE = deepcopy(GOOGLE_RESOURCE)
PUBSUB_RESOURCE.identifiers.append(
    ResourceIdentifier(key="pubsub", name="Pub/Sub", slug="pubsub")
)


class GooglePubSub(
    GoogleClientManager, Generic[PublisherConfigT, SubscriptionsConfigT], ABC
):
    def __init__(
        self,
        config: PubSubConfig[PublisherConfigT, SubscriptionsConfigT],
        log_config: LogConfig,
        *,
        application_context: OptApplicationContext = None,
        credentials: OptionalCredentials = None,
        credentials_path: OptPathOrStr = None,
    ) -> None:
        super().__init__(
            PUBSUB_RESOURCE.aggregate(),
            PUBSUB_RESOURCE.aggregate(AggregateField.NAME),
            log_config,
            application_context,
            credentials,
            credentials_path,
        )
        self._config = config
        self.publisher = PublisherClient(credentials=self._credentials)
        self.subscriber = SubscriberClient(credentials=credentials)
        self._active_listeners: Dict[str, StreamingPullFuture] = {}
        self._initialize_subscription_handlers()

    @abstractmethod
    def _initialize_subscription_handlers(self):
        """Initialize all subscription handlers"""

    @property
    @abstractmethod
    def subscription_handlers(self) -> Sequence[SubscriptionHandler]:
        """Define subscription handlers"""

    def _wait_for_async_result(
        self, *, future: asyncio.Future, timeout: float = 30.0
    ) -> bool:
        import time

        start_time = time.time()
        while not future.done() and (time.time() - start_time) < timeout:
            time.sleep(0.01)  # Small sleep to prevent busy waiting

        if future.done():
            try:
                return future.result()
            except Exception as e:
                self._logger.error(
                    "Exception occured while waiting for async controller result",
                    exc_info=True,
                    extra={"json_fields": {"exc_details": extract_details(e)}},
                )
                print(
                    f"Exception occured while waiting for async controller result:\n{traceback.format_exc()}"
                )
                return False
        else:
            self._logger.error("Timed out while waiting for async controller result")
            future.cancel()
            return False

    def _run_async_controller(
        self,
        subscription_id: str,
        message: Message,
        *,
        controller: MessageController[Coroutine[Any, Any, bool]],
    ) -> bool:
        """Run async controller function in a sync context"""
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we need to use run_coroutine_threadsafe
                # But since we're in a callback, we'll use a different approach
                future = asyncio.ensure_future(controller(subscription_id, message))
                # Wait for completion with timeout
                return self._wait_for_async_result(future=future)
            else:
                # Loop is not running, we can use run_until_complete
                return loop.run_until_complete(controller(subscription_id, message))
        except RuntimeError:
            # No event loop in current thread, create a new one
            return asyncio.run(controller(subscription_id, message))

    def message_callback(
        self,
        subscription_id: str,
        message: Message,
        *,
        controller: MessageController[R],
    ):
        """Main callback function which delegates to custom controllers or uses default processing"""
        # Check if the controller function is async
        if inspect.iscoroutinefunction(controller):
            # Handle async controller function
            success = self._run_async_controller(
                subscription_id, message, controller=controller
            )
        else:
            # Handle sync controller function
            success = controller(subscription_id, message)

        # Acknowledge or nack based on controller result
        prefix = f"Subscription {subscription_id} - Message {message.message_id}"
        log_extra = {
            "json_fields": {
                "pubsub_message": {
                    "id": message.message_id,
                    "attributes": dict(message.attributes),
                    "data": message.data.decode(),
                    "publish_time": message.publish_time.isoformat(),
                    "size": message.size,
                }
            }
        }
        if success:
            message.ack()
            self._logger.info(
                f"{prefix} - Successfully processed message", extra=log_extra
            )
        else:
            message.nack()
            self._logger.warning(
                f"{prefix} - Failed processing message", extra=log_extra
            )

    def _start_background_pull(self, future: StreamingPullFuture):
        try:
            pass
        except Exception as e:
            if not isinstance(e, asyncio.CancelledError):
                self._logger.error(
                    "Background pull ended with error",
                    exc_info=True,
                    extra={"json_fields": {"exc_details": extract_details(e)}},
                )
                print(f"Background pull ended with error:\n{traceback.format_exc()}")

    async def start_listening(self, *, handler: SubscriptionHandler):
        """Start listening to a specific subscription"""
        subscription_path = self.subscriber.subscription_path(
            self.project_id, handler.config.id
        )

        try:
            # Configure flow control
            flow_control = FlowControl(handler.config.max_messages)

            # Create streaming pull future with proper callback
            streaming_pull_future = self.subscriber.subscribe(
                subscription_path,
                lambda message: self.message_callback(
                    handler.config.id, message, controller=handler.controller
                ),
                flow_control,
                await_callbacks_on_shutdown=True,
            )

            self._active_listeners[subscription_path] = streaming_pull_future
            threading.Thread(
                target=self._start_background_pull,
                args=(streaming_pull_future,),
                daemon=True,
            ).start()

            self._logger.info(f"Started listener for subscription {subscription_path}")
        except Exception as e:
            self._logger.error(
                f"Exception occured while starting listener for subscription {subscription_path}",
                exc_info=True,
                extra={"json_fields": {"exc_details": extract_details(e)}},
            )
            print(
                f"Exception occured while starting listener for subscription {subscription_path}:\n{traceback.format_exc()}"
            )

    async def start_all_listeners(self):
        """Start listening to all subscriptions"""
        tasks = []
        for handler in self.subscription_handlers:
            task = asyncio.create_task(self.start_listening(handler=handler))
            tasks.append(task)

        # Wait for all listeners to be set up (not to complete)
        await asyncio.sleep(1)  # Give time for listeners to initialize

        self._logger.info(
            f"Started {len(self.subscription_handlers)} subscription listeners"
        )

        return tasks

    async def stop_all_listeners(self):
        """Stop all active listeners"""
        for _, future in self._active_listeners.items():
            future.cancel()
            try:
                future.result()
            except Exception:
                pass
        self._active_listeners.clear()

        self._logger.info(
            f"Stopped {len(self.subscription_handlers)} subscription listeners"
        )
