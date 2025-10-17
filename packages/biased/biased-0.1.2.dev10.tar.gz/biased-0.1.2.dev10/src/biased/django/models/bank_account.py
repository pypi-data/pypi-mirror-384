from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from biased.django.models.char_field import FixedLengthDigitsField
from biased.utils.aba_routing_number import is_aba_routing_number_valid


class BankAccountNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 20
        super().__init__(*args, **kwargs)


def _validate_aba_routing_number(value: str):
    if not is_aba_routing_number_valid(routing_number=value):
        raise ValidationError(
            _("%(value)s is not a valid ABA routing number"),
            params={"value": value},
            code="invalid_aba_routing_number",
        )


class AbaRoutingNumberField(FixedLengthDigitsField):
    def __init__(self, *args, **kwargs):
        kwargs["length"] = 9
        super().__init__(*args, **kwargs)
        self.validators.append(_validate_aba_routing_number)
