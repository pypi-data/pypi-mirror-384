from multiselectfield import MultiSelectField


class BiasedMultiSelectField(MultiSelectField):
    def get_prep_value(self, value):
        result = super().get_prep_value(value=value)
        return None if result == "" else result
