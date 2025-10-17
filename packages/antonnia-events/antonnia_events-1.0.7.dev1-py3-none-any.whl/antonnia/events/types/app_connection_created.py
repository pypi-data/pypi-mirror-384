"""MessageCreated event type."""

from typing import Literal
from pydantic import BaseModel

from .event_base import EventBase

# Import Message from conversations package
# This creates a dependency on antonnia-conversations
from antonnia.apps.types import AppConnection

class AppConnectionCreatedData(BaseModel):
    """Data payload for app.connection.created event."""
    
    object: AppConnection

class AppConnectionCreated(EventBase[AppConnectionCreatedData, Literal["app.connection.created"]]):
    """Event fired when a new app connection is created."""
    
    type: Literal["app.connection.created"] = "app.connection.created" 