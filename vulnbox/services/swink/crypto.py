from fish import FISH

import hashlib
import os

p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
A = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
B = 0x780e30db8d0bff9f35db5c169c4154566f784ac6c9f292c324f78692b59918e3

def _xor(a: bytes, b: bytes) -> bytes:
    res = []
    for i in range(max(len(a), len(b))):
        res.append(a[i % len(a)] ^ b[i % len(b)])

    return bytes(res)

def generate():
    x = int.from_bytes(os.urandom(32)) % p

    return x, (A*x**5 + B*x**3 + x + 1) % p


def sign(msg: str, skey: int):
    h = int.from_bytes(hashlib.sha256(msg.encode()).digest())
    k = int.from_bytes(os.urandom(32)) % p

    s = pow(k, -1, p) * (h*skey + 1) % p

    return hex(s)


def encrypt(msg: str, key: int):
    fish = FISH(key.to_bytes(32))

    return _xor(msg.encode(), fish.randbytes(len(msg.encode()))).hex()


def decrypt(msg: str, key: int):
    fish = FISH(key.to_bytes(32))

    return _xor(bytes.fromhex(msg), fish.randbytes(len(bytes.fromhex(msg)))).hex()
