from contextlib import contextmanager
from unittest.mock import patch

sms_send_post_method = "clicksend_client.api.sms_api.SMSApi.sms_send_post"
mms_send_post_method = "clicksend_client.api.mms_api.MMSApi.mms_send_post"
voice_send_post_method = "clicksend_client.api.voice_api.VoiceApi.voice_send_post"


@contextmanager
def mock_sms_send():
    with patch(sms_send_post_method) as mock:
        yield mock


@contextmanager
def mock_mms_send():
    with patch(mms_send_post_method) as mock:
        yield mock


@contextmanager
def mock_tts_send():
    with patch(voice_send_post_method) as mock:
        yield mock
