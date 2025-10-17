import re

# non-capturing inside octet regex
_OCTET_RE = r"(?:25[0-5]|2[0-4]\d|1?\d{1,2})"

# now only 5 groups: a, b, c, d, mask
IP_CIDR_RE = re.compile(
    rf"^({_OCTET_RE})\.({_OCTET_RE})\.({_OCTET_RE})\.({_OCTET_RE})/(8|16|24)$"
)

MASK_MAP = {
    8: "255.0.0.0",
    16: "255.255.0.0",
    24: "255.255.255.0",
}

def _ip_parts_to_str(a: int, b: int, c: int, d: int) -> str:
    return f"{a}.{b}.{c}.{d}"

def parse_ip(ip_string: str) -> dict:
    m = IP_CIDR_RE.match(ip_string.strip())
    if not m:
        return {}
    a, b, c, d, mask_bits = map(int, m.groups())  # now exactly 5
    ip_machine = _ip_parts_to_str(a, b, c, d)
    mask_bits = int(mask_bits)
    subnet_mask = MASK_MAP.get(mask_bits, "")
    if not subnet_mask:
        return {}
    if mask_bits == 8:
        network_address = _ip_parts_to_str(a, 0, 0, 0)
        broadcast_address = _ip_parts_to_str(a, 255, 255, 255)
    elif mask_bits == 16:
        network_address = _ip_parts_to_str(a, b, 0, 0)
        broadcast_address = _ip_parts_to_str(a, b, 255, 255)
    else:  # /24
        network_address = _ip_parts_to_str(a, b, c, 0)
        broadcast_address = _ip_parts_to_str(a, b, c, 255)

    return {
        "ip_machine": ip_machine,
        "subnet_mask": subnet_mask,
        "network_address": network_address,
        "broadcast_address": broadcast_address,
    }
