from clutchtimealerts.notifications.base import Notification
import requests
import os


class GroupMeNotification(Notification):
    COMMON_NAME = "GroupMe"
    BASE_URL = "https://api.groupme.com/v3/bots/post"

    def __init__(self, bot_id: str = None):
        if bot_id is None:
            bot_id = os.getenv("GROUPME_BOT_ID")
        self.bot_id = bot_id

    def send(self, message):
        data = {"bot_id": self.bot_id, "text": message}
        requests.post(url=self.BASE_URL, json=data)


if __name__ == "__main__":
    notification = GroupMeNotification()
    notification.send("test")
