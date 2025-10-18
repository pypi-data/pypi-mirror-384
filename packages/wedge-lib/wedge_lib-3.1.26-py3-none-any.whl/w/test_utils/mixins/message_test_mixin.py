import sms

from w.test_utils.serializers.technical_test_serializers import SmsMessageTestSerializer


class MessageTestMixin:
    # noinspection PyMethodMayBeStatic
    def setUp(self):
        super().setUp()
        self.reset_sms_outbox()

    def get_message_outbox(self):
        return sms.outbox

    def get_sms_sent(self):
        serializer = SmsMessageTestSerializer(sms.outbox, many=True)
        return serializer.data

    def get_mms_sent(self):
        # sms.backends.console.SmsBackend ne supporte pas MMS
        return self.get_sms_sent()

    def get_tts_sent(self):
        #  sms.backends.console.SmsBackend ne supporte pas les messages vocaux
        return self.get_sms_sent()

    @staticmethod
    def reset_sms_outbox():
        # empty sms
        sms.outbox = []
