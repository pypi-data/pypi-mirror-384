import json

from rest_framework import status

from w.drf.tests.api_testcase import ApiTestCase


class TestViewset(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.simple_valid = {
            "integer": 99,
            "string": "a string",
            "date": "2020-01-01",
        }
        cls.simple_invalid = {
            "integer": "a str",
            "string": 99,
            "date": 2020,
        }

    """
    POST simples/
    """

    def test_post_with_invalid_data_return_422(self):
        """Ensure invalid data returns 422"""
        url = self.reverse("simple-list")
        response = self.client_post(url, data=self.simple_invalid, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_post_with_success_return_201(self):
        """Ensure validation api succeeds"""
        url = self.reverse("simple-list")
        response = self.client_post(url, data=self.simple_valid, auth_by_token=False)
        self.assert_post_response(response)

    def test_post_with_context_with_invalid_data_return_201(self):
        """Ensure invalid data returns 422"""
        url = self.reverse("simple-with-context")
        response = self.client_post(url, data=self.simple_invalid, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_post_with_context_with_success_return_201(self):
        """Ensure validation api succeeds"""
        url = self.reverse("simple-with-context")
        response = self.client_post(url, data=self.simple_valid, auth_by_token=False)
        self.assert_post_response(response)

    def test_post_with_invalid_list_data_returns_422(self):
        """Ensure list invalid data returns 422"""
        url = self.reverse(
            "simple-multiple",
        )
        response = self.client_post(
            url,
            auth_by_token=False,
            data=json.dumps(
                [
                    {"not_integer": 2, "invalid_arg": "", "date": "2020-01-01"},
                    {"integer": 3, "string": "audi a1", "date": "2020-01-02"},
                ]
            ),
            content_type="application/json",
        )
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_post_with_list_data_with_success_return_201(self):
        """Ensure list validation is successful"""
        url = self.reverse(
            "simple-multiple",
        )
        response = self.client_post(
            url,
            auth_by_token=False,
            data=json.dumps(
                [
                    {"integer": 2, "string": "audi a4", "date": "2020-01-01"},
                    {"integer": 3, "string": "audi a1", "date": "2020-01-02"},
                ]
            ),
            content_type="application/json",
        )
        self.assert_rest_response(response, status=status.HTTP_201_CREATED)

    """
    POST simples/validate/?action=create
    """

    def test_validate_with_invalid_data_return_422(self):
        """Ensure validate is failed with invalid data"""
        url = self.reverse("simple-validate", query_params={"action": "create"})
        response = self.client_post(url, data=self.simple_invalid, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_validate_with_success_return_200(self):
        """Ensure validate is succeed with valid data"""
        url = self.reverse("simple-validate", query_params={"action": "create"})
        response = self.client_post(url, data=self.simple_valid, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_200_OK)

    """
    POST simples/?integer=<int>&string=<string>&date=<date>
    """

    def test_get_with_query_params_with_success_return_201(self):
        """Ensure validation is made with query parameters"""
        url = self.reverse(
            "simple-list",
            query_params={"integer": 2, "string": "audi a4", "date": "2020-01-01"},
        )
        response = self.client_post(url, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_201_CREATED)
