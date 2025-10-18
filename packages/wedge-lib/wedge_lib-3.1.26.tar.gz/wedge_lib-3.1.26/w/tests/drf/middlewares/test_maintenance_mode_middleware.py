from unittest.mock import patch
from rest_framework import status

from w.drf.tests.api_testcase import ApiTestCase


class TestMaintenanceModeMiddleware(ApiTestCase):
    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.simple_valid = {
            "integer": 99,
            "string": "a string",
            "date": "2020-01-01",
        }

    def test_call_with_maintenance_mode_off_return_response(self):
        with patch(
            target="w.services.technical.maintenance_mode_service."
            "MaintenanceModeService.is_on",
            return_value=False,
        ):
            url = self.reverse("simple-validate", query_params={"action": "create"})
            actual = self.client_post(url, data=self.simple_valid, auth_by_token=False)
            self.assert_rest_status_code(actual, status=status.HTTP_200_OK)
            self.assert_equals_resultset(actual.data)

    def test_call_with_maintenance_mode_on_return_503(self):
        with patch(
            target="w.services.technical.maintenance_mode_service."
            "MaintenanceModeService.is_on",
            return_value=True,
        ):
            url = self.reverse("simple-validate", query_params={"action": "create"})
            actual = self.client_post(url, data=self.simple_valid, auth_by_token=False)
            self.assert_rest_status_code(
                actual, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            self.assert_equals_resultset(actual.content)
