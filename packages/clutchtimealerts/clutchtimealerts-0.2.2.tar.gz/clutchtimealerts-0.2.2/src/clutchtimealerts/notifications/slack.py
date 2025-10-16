from clutchtimealerts.notifications.base import Notification
from slack_sdk import WebClient
import os


class SlackNotification(Notification):
    COMMON_NAME = "Slack"

    def __init__(self, token: str = None, channel: str = None):
        if token is None:
            token = os.getenv("SLACK_TOKEN")
        self.token = token

        if channel is None:
            channel = os.getenv("SLACK_CHANNEL")
        self.channel = channel

        self.client = WebClient(token=self.token)

    def send(self, message):
        self.client.chat_postMessage(channel=self.channel, text=message)


if __name__ == "__main__":
    notification = SlackNotification()
    notification.send("test")
