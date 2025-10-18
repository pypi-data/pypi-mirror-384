from rest_framework import status

from w.drf.tests.api_testcase import ApiTestCase
from w.tests.fixtures.datasets.builders.builder_with_internal_dependencies import (
    BuilderWithInternalDependencies,
)


class TestModelServiceViewset(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        list_builders = [BuilderWithInternalDependencies]
        cls.reset_sequence_builders(list_builders, reset_pk_model=False)
        cls.list = BuilderWithInternalDependencies().build_multiple(4)
        cls.post_data = BuilderWithInternalDependencies().build_post_data()

    """
    list
    """

    def test_list_with_success_return_200(self):
        """Ensure list succeeds"""
        url = self.reverse("model-list")
        response = self.client_get(url, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_200_OK)

    def test_list_with_query_params_return_200(self):
        """Ensure list with filters succeeds"""
        url = self.reverse("model-list", query_params={"name__contains": "name_1"})
        response = self.client_get(url, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_200_OK)

    def test_list_without_query_params_filter_return_200(self):
        """Ensure list succeeds without filtering by query params"""
        url = self.reverse(
            "model-list-without-qp-filter", query_params={"name__contains": "name_1"}
        )
        response = self.client_get(url, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_200_OK)

    """
    retrieve
    """

    def test_retrieve_with_success_return_200(self):
        """Ensure retrieve succeed"""
        url = self.reverse("model-detail", params={"pk": self.list[3].pk})
        response = self.client_get(url, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_200_OK)

    """
    create
    """

    def test_create_with_invalid_data_return_422(self):
        """Ensure invalid data return 422"""
        url = self.reverse("model-list")
        response = self.client_post(url, data={}, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_with_success_return_201(self):
        """Ensure create succeed"""
        url = self.reverse("model-list")
        response = self.client_post(url, data=self.post_data, auth_by_token=False)
        self.assert_post_response(response)

    """
    update
    """

    def test_update_with_invalid_data_return_422(self):
        """Ensure invalid data return 422"""
        url = self.reverse("model-detail", params={"pk": self.list[3].pk})
        response = self.client_put(url, data={}, auth_by_token=False)
        self.assert_rest_response(response, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_update_with_success_return_201(self):
        """Ensure create succeed"""
        url = self.reverse("model-detail", params={"pk": self.list[3].pk})
        response = self.client_put(url, data=self.post_data, auth_by_token=False)
        self.assert_put_response(response)

    """
    delete
    """

    def test_delete_with_success_return_204(self):
        """Ensure delete succeed"""
        url = self.reverse("model-detail", params={"pk": self.list[3].pk})
        response = self.client_delete(url, data=self.post_data, auth_by_token=False)
        self.assert_delete_response(response)
