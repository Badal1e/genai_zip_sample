import secrets


def generate_customer_id() -> str:
    return f"CUST{secrets.token_hex(4).upper()}"


def generate_acknowledgement_number() -> str:
    return f"ACK-{secrets.token_hex(3).upper()}-{secrets.randbelow(10**6):06d}"
