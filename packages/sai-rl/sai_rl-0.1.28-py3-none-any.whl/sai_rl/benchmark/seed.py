import hashlib
import hmac
import struct


def get_match_seed(master_int: int, index: int) -> int:
    master_key = master_int.to_bytes(32, "big")
    prk = hmac.new(b"\x00" * 32, master_key, hashlib.sha256).digest()
    info = struct.pack(">Q", index)
    t = b""
    okm = b""
    counter = 1
    while len(okm) < 8:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1
    return int.from_bytes(okm[:8], "big")
