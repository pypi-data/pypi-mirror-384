import serpy


class SmsMessageTestSerializer(serpy.Serializer):
    body = serpy.Field()
    originator = serpy.Field()
    recipients = serpy.MethodField()

    def get_recipients(self, obj):
        return [r for r in obj.recipients]
