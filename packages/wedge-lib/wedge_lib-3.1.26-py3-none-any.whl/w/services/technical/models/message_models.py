from sms import Message


class Sms(Message): ...


class Mms(Message):
    def __init__(self, *args, media_url: str, **kwargs):
        self.media_url = media_url
        super().__init__(*args, **kwargs)


class Tts(Message): ...
