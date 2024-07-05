import datetime


class PrivateMessage:
    def __init__(
            self,
            sender,
            sender_realm,
            receiver,
            receiver_realm,
            message
    ):
        self.sender = sender
        self.sender_realm = sender_realm
        self.receiver = receiver
        self.receiver_realm = receiver_realm
        self.message = message
        self.created_at = str(datetime.datetime.now())

    def toDict(self):
        return vars(self)
