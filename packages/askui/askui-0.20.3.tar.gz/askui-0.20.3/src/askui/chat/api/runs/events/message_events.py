from typing import Literal

from askui.chat.api.messages.models import Message
from askui.chat.api.runs.events.event_base import EventBase


class MessageEvent(EventBase):
    data: Message
    event: Literal["thread.message.created"]
