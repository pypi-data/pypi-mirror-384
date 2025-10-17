from collections.abc import Callable
from functools import update_wrapper
from typing import Any

from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.db.models import Model
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from biased.django.utils.reverse import reverse_querystring


def _id_admin_change_url(app_label: str, model_name: str, object_id: str, id_slug: str | None = None) -> str:
    if id_slug is None:
        url_name = f"admin:{app_label}_{model_name}_change"
    else:
        url_name = f"admin:{app_label}_{model_name}_{id_slug}_change"

    return reverse(url_name, kwargs=dict(object_id=object_id))


def admin_change_url(instance: Model):
    app_label = instance._meta.app_label  # pylint: disable=protected-access
    model_name = instance._meta.model.__name__.lower()  # pylint: disable=protected-access
    return _id_admin_change_url(app_label=app_label, model_name=model_name, object_id=instance.pk)


def admin_change_html_link(instance: Model):
    url = admin_change_url(instance)
    return format_html('<a href="{}">{}</a>', url, instance)


def _id_admin_change_html_link(app_label: str, model_name: str, object_id: str, id_slug: str | None = None) -> str:
    url = _id_admin_change_url(app_label=app_label, model_name=model_name, object_id=object_id, id_slug=id_slug)
    return format_html('<a href="{}">{}</a>', url, object_id)


def admin_change_link(short_description: str, empty_description: str = "-"):
    def wrapper(func):
        def field_func(self, obj):
            related_obj = func(self, obj)
            if related_obj is None:
                return empty_description
            return admin_change_html_link(instance=related_obj)

        field_func.short_description = short_description
        return field_func

    return wrapper


def id_admin_change_link(
    short_description: str, app_label: str, model_name: str, id_slug: str | None = None, empty_description: str = "-"
):
    def wrapper(func):
        def field_func(self, obj):
            object_id = func(self, obj)
            if object_id is None:
                return empty_description
            return _id_admin_change_html_link(
                app_label=app_label, model_name=model_name, object_id=object_id, id_slug=id_slug
            )

        field_func.short_description = short_description
        return field_func

    return wrapper


def _admin_query_params_list_url(model_type: type[Model], query_kwargs: dict) -> str:
    url_name = f"admin:{model_type._meta.app_label}_{model_type._meta.model_name}_changelist"
    return reverse_querystring(url_name, query_kwargs=query_kwargs)


def _admin_query_params_list_html_link(
    model_type: type[Model], title: str, query_kwargs: dict, target: str = "_self"
) -> str:
    url = _admin_query_params_list_url(model_type=model_type, query_kwargs=query_kwargs)
    return format_html('<a href="{url}" target="{target}">{title}</a>', url=url, title=title, target=target)


def admin_query_params_list_link(
    short_description: str, model_type: type[Model], empty_description: str = "-", target: str = "_self"
):
    def wrapper(func: Callable[[ModelAdmin, Model], tuple[str, dict]]):
        def field_func(self, obj):
            title, query_params = func(self, obj)
            if title is None:
                return empty_description
            return _admin_query_params_list_html_link(
                model_type=model_type, title=title, query_kwargs=query_params, target=target
            )

        field_func.short_description = short_description
        return field_func

    return wrapper


def _build_html_image_tag(url: str, attributes: dict[str, Any] | None = None) -> str:
    if attributes:
        attributes_html = mark_safe(" ".join(f'{attr}="{value}"' for attr, value in attributes.items()))  # nosec B308:blacklist, B703:django_mark_safe
    else:
        attributes_html = ""
    return format_html('<img src="{url}" {attributes_html}/>', url=url, attributes_html=attributes_html)


def html_image_tag(short_description: str, attributes: dict[str, Any] | None = None, empty_description: str = "-"):
    def wrapper(func):
        def field_func(self, obj):
            image_url = func(self, obj)
            if image_url is None:
                return empty_description
            return _build_html_image_tag(url=image_url, attributes=attributes)

        field_func.short_description = short_description
        return field_func

    return wrapper


def url_link(short_description: str, content: str = "-", target: str = "_self"):
    def wrapper(func: Callable[[ModelAdmin, Model], dict[str, str] | None]):
        def field_func(self, obj):
            result = func(self, obj)
            if result is None:
                return content
            else:
                params = dict(content=content, target=target)
                params.update(func(self, obj))
                return format_html('<a href="{url}" target="{target}">{content}</a>', **params)

        field_func.short_description = short_description
        return field_func

    return wrapper


class ReadOnlyModelAdminMixin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyInlineMixin(InlineModelAdmin):
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ChangeFormActionMixin(ModelAdmin):
    change_form_template = "actions_change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        actions = self.get_actions(request)
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields["action"].choices = self.get_action_choices(request)
            extra_context["action_form"] = action_form
        return super().change_view(request, object_id, form_url, extra_context)


class ExternalIdModelAdmin(ModelAdmin):
    def external_id_change_view(self, request, object_id, form_url="", extra_context=None):
        try:
            object_pk = str(self.model.objects.get(external_id=object_id).pk)
        except self.model.DoesNotExist:
            return self._get_obj_does_not_exist_redirect(request, self.opts, object_id)
        return self.changeform_view(request, object_pk, form_url, extra_context)

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        urls = super().get_urls()

        external_id_urls = [
            path(
                "external_id/<path:object_id>/change/",
                wrap(self.external_id_change_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_external_id_change",
            ),
        ]
        return external_id_urls + urls
