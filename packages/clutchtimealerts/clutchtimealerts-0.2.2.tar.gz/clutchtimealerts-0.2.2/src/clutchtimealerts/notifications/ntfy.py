from clutchtimealerts.notifications.base import Notification
import requests
import os


class NtfyNotification(Notification):
    COMMON_NAME = "Ntfy"

    def __init__(self, host: str = None, topic: str = None, token: str = None):
        if host is None:
            host = os.getenv("NTFY_HOST", "https://ntfy.sh")
        self.host = host

        if topic is None:
            topic = os.getenv("NTFY_TOPIC")
        self.topic = topic

        if token is None:
            token = os.getenv("NTFY_TOKEN")
        self.token = token

        if self.topic is None:
            raise ValueError("Topic not specified")

        self.url = f"{self.host}/{self.topic}"

    def send(self, message):
        # SEt header if necessary
        if self.token is None:
            headers = None
        else:
            headers = {"Authorization": "Bearer " + self.token}

        # Post noitifications
        r = requests.post(self.url, data=message, headers=headers)

        if r.status_code != 200:
            raise Exception(
                f"Failed to send notification: (Code: {r.status_code}) {r.text}"
            )


if __name__ == "__main__":
    notification = NtfyNotification()
    notification.send("test")
