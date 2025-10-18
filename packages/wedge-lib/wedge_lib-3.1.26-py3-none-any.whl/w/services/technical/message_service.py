import logging

from w.services.abstract_service import AbstractService
from w.services.technical.models.message_models import Message, Sms, Mms, Tts

logger = logging.getLogger("django")


class MessageService(AbstractService):
    @classmethod
    def _send(cls, message: Message) -> None:
        try:
            message.send(fail_silently=False)
        except Exception as exc:
            logger.error(f"Send message failed: {exc}")

    @classmethod
    def send_sms(cls, message: str, recipients: list[str]) -> None:
        logger.info(f"Send SMS to {', '.join(recipients)}")
        logger.info(message)
        sms = Sms(body=message, recipients=recipients)
        cls._send(sms)

    @classmethod
    def send_mms(cls, message: str, recipients: list[str], media_url: str) -> None:
        logger.info(f"Send MMS to {', '.join(recipients)}")
        logger.info(message)
        mms = Mms(body=message, recipients=recipients, media_url=media_url)
        cls._send(mms)

    @classmethod
    def send_tts(cls, message: str, recipients: list[str]) -> None:
        logger.info(f"Send TTS message to {', '.join(recipients)}")
        logger.info(message)
        tts = Tts(body=message, recipients=recipients)
        cls._send(tts)
