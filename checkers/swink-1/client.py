#!/usr/bin/env python3
import os
os.environ["PWNLIB_NOTERM"] = "1"

from pwn import remote
import json
import logging
import string

logging.disable()

TEXT_FIELDS = ('title', 'description')
PRINTABLE = set(string.printable)


def _decode_hex_text(value):
    if not isinstance(value, str):
        return value

    try:
        decoded = bytes.fromhex(value).decode()
    except (ValueError, UnicodeDecodeError):
        return value

    if all(char in PRINTABLE for char in decoded):
        return decoded

    return value


def _decode_private_transactions(txs):
    if not isinstance(txs, list):
        return txs

    for tx in txs:
        if not isinstance(tx, dict):
            continue
        for field in TEXT_FIELDS:
            tx[field] = _decode_hex_text(tx.get(field))

    return txs

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False

    def connect(self):
        self.remote = remote(self.host, self.port)
        self.connected = True

    def close(self):
        if self.connected:
            self.remote.close()
            self.connected = False

    def sync(self):
        if self.connected:
            self.remote.recvuntil(b'Choice: ', timeout=5)

    def _cmd(self, choice, prompts):
        if not self.connected:
            return False

        self.remote.sendline(choice)
        try:
            for prompt, data in prompts:
                self.remote.recvuntil(prompt, timeout=5)
                self.remote.sendline(data)

            res = self.remote.recvline(timeout=5).strip()
            self.sync()
            return b'ok' in res
        except:
            self.close()
            return False

    def register(self, username: bytes, password: bytes) -> bool:
        return self._cmd(b'1', [(b'username: ', username), (b'password: ', password)])

    def login(self, username: bytes, password: bytes) -> bool:
        return self._cmd(b'2', [(b'username: ', username), (b'password: ', password)])

    def logout(self) -> bool:
        return self._cmd(b'3', [])

    def deposit(self, title: bytes, desc: bytes, amount: int) -> bool:
        return self._cmd(b'4', [(b'title: ', title), (b'description: ', desc), (b'amount: ', str(amount).encode())])

    def withdraw(self, title: bytes, desc: bytes, amount: int) -> bool:
        return self._cmd(b'5', [(b'title: ', title), (b'description: ', desc), (b'amount: ', str(amount).encode())])

    def gift(self, target: bytes, title: bytes, desc: bytes, amount: int) -> bool:
        return self._cmd(b'6', [(b'to (username): ', target), (b'title: ', title), (b'description: ', desc), (b'amount: ', str(amount).encode())])

    def _get_json(self, choice, prompts):
        if not self.connected:
            return None
        self.remote.sendline(choice)
        try:
            for prompt, data in prompts:
                self.remote.recvuntil(prompt, timeout=5)
                self.remote.sendline(data)

            blob = self.remote.recvuntil(b'\n[', drop=True, timeout=5)
            self.remote.recvuntil(b'Choice: ', timeout=5)

            if b'err:' in blob:
                return None

            start = blob.find(b'[') if choice == b'7' else blob.find(b'{')
            data = json.loads(blob[start:])
            if choice == b'7':
                return _decode_private_transactions(data)
            return data
        except:
            self.close()
            return None

    def my_transactions(self) -> list | None:
        return self._get_json(b'7', [])

    def user_transactions(self, username: bytes) -> dict | None:
        return self._get_json(b'8', [(b'username: ', username)])
