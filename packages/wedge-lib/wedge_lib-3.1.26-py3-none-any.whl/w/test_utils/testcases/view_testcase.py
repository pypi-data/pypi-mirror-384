from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBase

from w.django.tests.django_testcase import DjangoTestCase
from w.django.tests.factories.auth_factories import UserFactory
from w.django.utils import reverse


class ViewTestCase(DjangoTestCase):
    """Class to handle common View test functionalities"""

    def _get_user(self):
        if self.default_user is None:
            self.default_user = UserFactory(
                username="factory-boy",
                first_name="Factory",
                last_name="Boy",
                email="fb@factory.com",
            )
        return self.default_user

    def force_login(self, user=None):
        """
        Force login, if no user given, use a default one
        (created via factory_boy)

        Args:
            user (User): user to authenticate (optional)
        """
        if user is None:
            user = self._get_user()
        self.client.force_login(user=user)

    def _client_method(self, method, url, force_login, data=None, user=None, **extra):
        params = {"path": url, "data": data}
        if force_login:
            self.force_login(user)
        return getattr(self.client, method)(**{**params, **extra})

    def client_get(self, url, user=None, force_login=True):
        return self._client_method("get", url, force_login, user=user)

    def client_post(self, url, data=None, user=None, force_login=True):
        return self._client_method("post", url, force_login, data=data, user=user)

    def client_ajax_get(self, url, user=None, force_login=True):
        return self._client_method(
            "get",
            url,
            force_login,
            user=user,
            HTTP_ACCEPT="text/html, */*; q=0.01",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def client_ajax_post(self, url, data=None, user=None, force_login=True):
        return self._client_method(
            "post",
            url,
            force_login,
            data=data,
            user=user,
            HTTP_ACCEPT="text/html, */*; q=0.01",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    @staticmethod
    def assert_response_status(response: HttpResponse, status_code=200):
        """Assert response status"""
        assert response.status_code == status_code

    @staticmethod
    def assert_redirect(response: HttpResponseBase, redirect_url=None):
        """Assert response is redirect with url"""
        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HttpResponseRedirect.status_code
        if redirect_url is not None:
            assert response.url == redirect_url, f"{response.url} != {redirect_url}"

    def assert_redirect_login(self, response, redirect_url):
        self.assert_redirect(response, f"{reverse('login')}?next={redirect_url}")

    def assert_get_with_unauthenticated_user_redirect_login(self, url):
        """Assert get with unauthenticated user is redirected to login"""
        response = self.client_get(url, force_login=False)
        self.assert_redirect_login(response, url)

    def assert_post_with_unauthenticated_user_redirect_login(self, url):
        """Assert post with unauthenticated user is redirected to login"""
        response = self.client_post(url, data={"param": "value"}, force_login=False)
        self.assert_redirect_login(response, url)
