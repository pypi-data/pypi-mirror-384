INT16_MAX = (1 << 15) - 1

def signed_to_unsigned2(signed: int) -> int:
    return signed & 0xFFFF

def unsigned_to_signed2(unsigned: int) -> int:
    return (unsigned & ((1 << 15) - 1)) - (unsigned & (1 << 15))

def signed_to_unsigned4(signed: int) -> int:
    return signed & 0xFFFFFFFF

def unsigned_to_signed4(unsigned: int) -> int:
    return (unsigned & ((1 << 31) - 1)) - (unsigned & (1 << 31))

# arduino style map function
def map_value(val, from_low: float, from_high: float, to_low: float, to_high: float) -> float:
    return (val - from_low) / (from_high - from_low) * (to_high - to_low) + to_low