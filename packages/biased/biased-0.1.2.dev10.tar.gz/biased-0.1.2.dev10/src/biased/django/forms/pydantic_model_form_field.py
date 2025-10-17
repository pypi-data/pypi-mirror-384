import pydantic
from django import forms
from django.core.exceptions import ValidationError
from django.forms import JSONField, Textarea
from django.forms.fields import InvalidJSONInput
from pydantic import BaseModel


# Consider to use [django-pydantic-field](https://github.com/surenkov/django-pydantic-field) instead
class PydanticModelFormField(JSONField):
    default_error_messages = {
        "invalid": "Enter a valid JSON.",
        "invalid_schema": "Data has invalid schema. %(pydantic_error)s.",
    }

    widget = Textarea

    def __init__(self, pydantic_model: type[BaseModel], encoder=None, decoder=None, **kwargs):
        self.pydantic_model = pydantic_model
        super().__init__(encoder=encoder, decoder=decoder, **kwargs)

    def _value_to_pydantic_model(self, value):
        try:
            value = self.pydantic_model.model_validate(value, from_attributes=True)
        except pydantic.ValidationError as e:
            raise ValidationError(
                self.error_messages["invalid_schema"],
                code="invalid_schema",
                params=dict(
                    pydantic_error=str(e),
                ),
            ) from e
        return value

    def to_python(self, value):
        value = super().to_python(value)
        value = self._value_to_pydantic_model(value)
        return value

    def bound_data(self, data, initial):
        value = super().bound_data(data, initial)
        if isinstance(value, InvalidJSONInput):
            return value
        try:
            return self._value_to_pydantic_model(value)
        except ValidationError:
            return InvalidJSONInput(data)

    def prepare_value(self, value):
        if value is None:
            return None
        if isinstance(value, InvalidJSONInput):
            return value
        if isinstance(value, self.pydantic_model):
            value = value.dict()
        return super().prepare_value(value)

    def has_changed(self, initial, data):
        return forms.Field.has_changed(self, initial, data)
