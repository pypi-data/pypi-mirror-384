def filter_not_none_values(value: dict) -> dict:
    return {key: value for key, value in value.items() if value is not None}
