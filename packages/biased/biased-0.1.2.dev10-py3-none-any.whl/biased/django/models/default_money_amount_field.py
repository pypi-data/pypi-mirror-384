from django.db import models


class DefaultMoneyAmountField(models.DecimalField):
    def __init__(self, max_digits=10, decimal_places=2, **kwargs):
        super().__init__(max_digits=max_digits, decimal_places=decimal_places, **kwargs)
