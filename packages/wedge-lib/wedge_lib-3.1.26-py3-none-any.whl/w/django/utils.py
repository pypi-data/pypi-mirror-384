from django import urls
from django.utils.translation import gettext

from django.db import models
from django.db.models.fields.related import ManyToManyField, ForeignKey


# noinspection PyUnresolvedReferences,PyProtectedMember
def model_to_dict(model: models.Model):
    if hasattr(model, "_meta") is False:  # pragma: no cover (todo one day)
        return None
    opts = model._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ForeignKey):
            fk = getattr(model, f.name)
            data[f.name] = model_to_dict(getattr(model, f.name)) if fk else None
            continue
        if isinstance(f, ManyToManyField):
            data[f.name] = [model_to_dict(m) for m in f.value_from_object(model)]
            continue
        data[f.name] = f.value_from_object(model)
    return data


def reverse(
    viewname, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None
):
    """ "
    Url reverse extending django.urls.reverse to handle query_params

    Usage:
        reverse(
            <url_name>,
            kwargs={'pk': 123},
            query_kwargs={'key':'value', 'k2': 'v2'}
        )
    """
    base_url = urls.reverse(
        viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
    )

    if query_kwargs:
        from w.services.technical.url_service import UrlService

        return f"{base_url}?{UrlService.get_url_query_string(**query_kwargs)}"

    return base_url


def _(message):
    """
    deprecated translation shortcut => old bad ideas
    better to use: from django.utils.translation import gettext as _
    """
    return gettext(message)


def list_accepted_types(request):  # pragma: no cover (todo one day)
    """List accepted types of HttpRequest"""
    return [a.split(";")[0] for a in request.META["HTTP_ACCEPT"].split(",")]


def is_request_accept_json(request):  # pragma: no cover (todo one day)
    """Check if request accept json response"""
    accepted_type = list_accepted_types(request)
    return "application/json" in accepted_type or "text/javascript" in accepted_type


def is_request_accept_html(request):  # pragma: no cover (todo one day)
    """Check if request accept html response"""
    accepted_type = list_accepted_types(request)
    return "text/html" in accepted_type


def is_request_accept_all(request):  # pragma: no cover (todo one day)
    """Check if request accept all response"""
    accepted_type = list_accepted_types(request)
    return "*/*" in accepted_type
