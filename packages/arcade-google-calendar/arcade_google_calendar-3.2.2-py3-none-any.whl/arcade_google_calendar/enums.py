from enum import Enum


class EventVisibility(Enum):
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class SendUpdatesOptions(Enum):
    NONE = "none"  # No notifications are sent
    ALL = "all"  # Notifications are sent to all guests
    EXTERNAL_ONLY = "externalOnly"  # Notifications are sent to non-Google Calendar guests only.


class UpdateGoogleMeetOptions(Enum):
    NONE = "none"  # No Google Meet is added
    ADD = "add"  # Google Meet is added
    REMOVE = "remove"  # Google Meet is removed
