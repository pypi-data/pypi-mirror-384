from google.cloud.pubsub_v1.subscriber.message import Message
from typing import Callable, TypeVar


R = TypeVar("R")
MessageController = Callable[[str, Message], R]
