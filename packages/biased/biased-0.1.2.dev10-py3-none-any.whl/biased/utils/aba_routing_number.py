def is_aba_routing_number_valid(routing_number: str) -> bool:
    if not routing_number.isdigit() or len(routing_number) != 9:
        return False

    digits = map(int, routing_number)
    weights = (3, 7, 1, 3, 7, 1, 3, 7, 1)
    checksum = sum(d * w for d, w in zip(digits, weights, strict=True))
    return checksum % 10 == 0


def validate_aba_routing_number(value: str) -> str:
    if not is_aba_routing_number_valid(routing_number=value):
        raise ValueError(f'Invalid ABA Routing Number "{value}"')
    return value
