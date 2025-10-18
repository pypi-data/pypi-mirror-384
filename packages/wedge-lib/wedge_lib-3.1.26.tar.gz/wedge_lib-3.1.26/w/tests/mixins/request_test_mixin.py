from w.services.technical.json_service import JsonService


class RequestTestMixin:
    @classmethod
    def get_request_mock_calls(cls, mock):
        calls = cls.get_mock_calls(mock)
        for call in calls:
            kwargs = call.get("kwargs", None)
            if kwargs is None:
                continue
            data = kwargs.get("data", None)
            if data is None:
                continue

            call["kwargs"]["data"] = JsonService.load_from_str(data)

        return calls
