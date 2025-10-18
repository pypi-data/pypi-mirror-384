import abc

from rest_framework import status

from w.django.utils import reverse


# noinspection PyUnresolvedReferences
class ApiViewSetMixin:
    resource = None
    _calling_filename = None

    @staticmethod
    @abc.abstractmethod
    def get_resource_objects():
        pass

    @classmethod
    def get_resource_pk(cls):
        return getattr(cls, cls.resource).pk

    @classmethod
    def get_post_data_resource(cls):
        return getattr(cls, "get_rest_data_%s" % cls.resource)(rest_method="POST")

    @classmethod
    def get_put_data_resource(cls):
        return getattr(cls, "get_rest_data_%s" % cls.resource)(rest_method="PUT")

    @classmethod
    def get_patch_data_resource(cls):
        return getattr(cls, "get_rest_data_%s" % cls.resource)(rest_method="PATCH")

    """
    GET /{resources}
    """

    def _list_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot get resource if no user authenticated
        """
        self.assert_get_with_no_registered_user_return_401("%s-list" % self.resource)

    def _list_resource_with_success_return_200(self, user=None):
        """
        Ensure we can get all resources
        """
        url = reverse("%s-list" % self.resource)
        response = self.client_get(url, user=user)
        self.assert_get_response(response, calling_filename=self._calling_filename)

    def _list_resource_return_405(self):
        """
        Ensure we cannot list all resources
        """
        url = reverse("%s-list" % self.resource)
        response = self.client_get(url)
        self.assert_rest_status_code(response, status.HTTP_405_METHOD_NOT_ALLOWED)

    """
    GET /{resources}/{pk}
    """

    def _get_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot get resource if no user authenticated
        """
        self.assert_get_with_no_registered_user_return_401(
            "%s-detail" % self.resource, {"pk": 1}
        )

    def _get_resource_with_success_return_200(self, user=None):
        """
        Ensure we can get a resource
        """
        url = reverse(
            "%s-detail" % self.resource, kwargs={"pk": self.get_resource_pk()}
        )
        response = self.client_get(url, user=user)
        self.assert_get_response(response, calling_filename=self._calling_filename)

    def _get_resource_with_me_return_200(self, user=None):
        """
        Ensure we can get resource linked to current user
        """
        url = reverse("%s-detail" % self.resource, kwargs={"pk": "me"})
        response = self.client_get(url, user=user)
        self.assert_get_response(response, calling_filename=self._calling_filename)

    """
    POST /{resources}
    """

    def _post_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot post resource if no user authenticated
        """
        self.assert_post_with_no_registered_user_return_401("%s-list" % self.resource)

    def _post_resource_with_success_return_201(self, user=None):
        """
        Ensure we can post resource
        """
        url = reverse("%s-list" % self.resource)
        data = self.get_post_data_resource()
        response = self.client_post(url, data=data, user=user)
        self.assert_post_response(
            data, response, calling_filename=self._calling_filename
        )

    """
    PUT /{resources}/{pk}
    """

    def _put_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot put resource if no user authenticated
        """
        self.assert_put_with_no_registered_user_return_401(
            "%s-detail" % self.resource, {"pk": 1}
        )

    def _put_resource_with_success_return_200(self, user=None):
        """
        Ensure we can put a resource
        """
        url = reverse(
            "%s-detail" % self.resource, kwargs={"pk": self.get_resource_pk()}
        )
        data = self.get_put_data_resource()
        response = self.client_put(url, data=data, user=user)
        self.assert_put_response(
            self.get_resource_pk(),
            data,
            response,
            calling_filename=self._calling_filename,
        )

    """
    PATCH /{resources}/{pk}
    """

    def _patch_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot patch resource if no user authenticated
        """
        self.assert_put_with_no_registered_user_return_401(
            "%s-detail" % self.resource, {"pk": 1}
        )

    def _patch_resource_with_success_return_200(self, user=None):
        """
        Ensure we can patch a resource
        """
        url = reverse(
            "%s-detail" % self.resource, kwargs={"pk": self.get_resource_pk()}
        )
        data = self.get_patch_data_resource()
        response = self.client_patch(url, data=data, user=user)
        self.assert_patch_response(
            self.get_resource_pk(),
            data,
            response,
            calling_filename=self._calling_filename,
        )

    """
    DEL /{resources}/{pk}
    """

    def _del_resource_with_no_registered_user_return_401(self):
        """
        Ensure we cannot delete resource if no user authenticated
        """
        self.assert_delete_with_no_registered_user_return_401(
            "%s-detail" % self.resource, {"pk": 1}
        )

    def _del_issue_with_success_return_204(self, user=None):
        """
        Ensure we can delete an issue
        """
        url = reverse(
            "%s-detail" % self.resource, kwargs={"pk": self.get_resource_pk()}
        )
        response = self.client_delete(url, user=user)
        self.assert_delete_response(self.get_resource_pk(), response)
