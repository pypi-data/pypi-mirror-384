from urllib.parse import urlencode

from django.urls import reverse


def reverse_querystring(viewname: str, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None):
    """
    Custom Django reverse function to handle query strings.
    Usage:
        reverse('app.views.my_view', kwargs={'pk': 123}, query_kwargs={'search', 'Bob'})
    """
    base_url = reverse(viewname=viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
    if query_kwargs:
        return f"{base_url}?{urlencode(query_kwargs)}"
    return base_url
