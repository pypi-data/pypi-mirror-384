import pydantic
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from pydantic import BaseModel

from biased.django.forms.pydantic_model_form_field import PydanticModelFormField
from biased.utils.default_json_encoder import DefaultJsonEncoder


# Consider to use [django-pydantic-field](https://github.com/surenkov/django-pydantic-field) instead
class PydanticModelField(JSONField):
    default_error_messages = {
        "invalid": "Value must be valid JSON.",
        "invalid_schema": "Data has invalid schema. %(pydantic_error)s",
    }

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

    def validate(self, value, model_instance):
        if isinstance(value, self.pydantic_model):
            return
        self._value_to_pydantic_model(value)
        super().validate(value, model_instance)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": PydanticModelFormField,
                "pydantic_model": self.pydantic_model,
                "encoder": self.encoder,
                "decoder": self.decoder,
                **kwargs,
            }
        )

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        self._value_to_pydantic_model(value)
        return value

    def __init__(self, pydantic_model: type[BaseModel], *args, **kwargs):
        self.pydantic_model = pydantic_model
        kwargs.setdefault("encoder", DefaultJsonEncoder)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["pydantic_model"] = self.pydantic_model
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if value is None:
            return None
        value = self._value_to_pydantic_model(value)
        return value

    def get_prep_value(self, value):
        if isinstance(value, BaseModel):
            value = value.model_dump()
        return super().get_prep_value(value)
