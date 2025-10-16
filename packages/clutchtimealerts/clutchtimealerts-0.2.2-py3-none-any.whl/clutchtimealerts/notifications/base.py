from abc import ABC, abstractmethod
from dataclasses import dataclass


class Notification(ABC):
    COMMON_NAME = "Notification"

    @abstractmethod
    def send(self, message):
        pass


@dataclass
class NotificationConfig:
    notification: Notification
    notification_format: str
    ot_format: str
    nba_teams: set[str]
    preseason: bool = False
