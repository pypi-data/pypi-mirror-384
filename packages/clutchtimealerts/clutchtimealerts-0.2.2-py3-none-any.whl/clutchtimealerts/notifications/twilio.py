from clutchtimealerts.notifications.base import Notification
from twilio.rest import Client
import os


class TwilioNotification(Notification):
    COMMON_NAME = "Twilio"

    def __init__(
        self,
        account_sid: str = None,
        auth_token: str = None,
        sender_number: str = None,
        receiving_numbers: list[str] = None,
    ):
        if account_sid is None:
            self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        if auth_token is None:
            self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if sender_number is None:
            self.sender_number = os.getenv("TWILIO_SENDER_NUMBER")
        if receiving_numbers is None:
            self.receiving_numbers = os.getenv("TWILIO_RECEIVING_NUMBERS")
            print(self.receiving_numbers)
            if self.receiving_numbers is not None:
                self.receiving_numbers = self.receiving_numbers.split(",")
            else:
                self.receiving_numbers = []

        if self.receiving_numbers == []:
            raise ValueError("No receiving numbers specified")

        if self.sender_number is None:
            raise ValueError("Sender number not specified")

        if self.account_sid is None:
            raise ValueError("Account SID not specified")

        if self.auth_token is None:
            raise ValueError("Auth token not specified")

        self.client = Client(account_sid, auth_token)

    def send(self, message):
        for number in self.receiving_numbers:
            self.client.messages.create(
                body=message, from_=self.sender_number, to=number
            )


if __name__ == "__main__":
    notification = TwilioNotification()
    notification.send("test")
