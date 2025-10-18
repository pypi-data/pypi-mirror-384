from w.test_utils.helpers import date_test_helper


class CypressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today_is = request.META.get("HTTP_CYPRESS_TODAY_IS", None)
        if today_is is None:
            return self.get_response(request)

        with date_test_helper.today_is(today_is):
            response = self.get_response(request)
        return response
