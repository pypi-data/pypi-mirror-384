import logging
from contextlib import contextmanager
from typing import ContextManager, Iterable
from uuid import uuid4

from clicksend_client import (
    ApiClient,
    Configuration,
    MMSApi,
    MmsMessage,
    MmsMessageCollection,
    SMSApi,
    SmsMessage,
    SmsMessageCollection,
    VoiceApi,
    VoiceMessage,
    VoiceMessageCollection,
)
from django.conf import settings
from sms.backends.base import BaseSmsBackend

from w.services.technical.models.message_models import Message, Mms, Tts

logger = logging.getLogger("django")


class ClickSendBackend(BaseSmsBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        configuration = Configuration()
        configuration.username = settings.CLICKSEND_USERNAME
        configuration.password = settings.CLICKSEND_API_KEY
        self.client = ApiClient(configuration)

    def send_messages(self, messages: Iterable[Message]) -> int:
        message_count: int = 0

        for message in messages:
            with self._error_handler():
                self.send_message(message)
                message_count += len(message.recipients)

        return message_count

    def send_message(self, message: Message):
        if isinstance(message, Tts):
            self._send_tts(message)
        elif isinstance(message, Mms):
            self._send_mms(message)
        else:
            self._send_sms(message)

    def _send_sms(self, message: Message):
        api = SMSApi(self.client)
        messages = SmsMessageCollection(
            messages=[
                SmsMessage(body=message.body, to=recipient)
                for recipient in message.recipients
            ],
        )
        api.sms_send_post(messages)

    def _send_mms(self, message: Mms):
        api = MMSApi(self.client)
        messages = MmsMessageCollection(
            media_file=message.media_url,
            messages=[
                MmsMessage(subject="Api", body=message.body, to=recipient)
                for recipient in message.recipients
            ],
        )
        api.mms_send_post(messages)

    def _send_tts(self, message: Tts):
        api = VoiceApi(self.client)
        custom_string = uuid4().hex
        messages = VoiceMessageCollection(
            messages=[
                VoiceMessage(
                    body=message.body,
                    to=recipient,
                    lang="fr-fr",
                    voice="female",
                    custom_string=custom_string,
                    machine_detection=1,
                    country="france",
                )
                for recipient in message.recipients
            ],
        )
        api.voice_send_post(messages)

    @contextmanager
    def _error_handler(self) -> ContextManager[None]:
        try:
            yield None
        except Exception as exc:
            if not self.fail_silently:
                raise exc

            logger.error(str(exc))
