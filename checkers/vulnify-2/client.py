#!/usr/bin/env python3
import os
os.environ["PWNLIB_NOTERM"] = "1"

from pwn import remote
import json

import logging
logging.disable()


class Client():
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

    def exit(self):
        if self.connected:
            self.remote.recvuntil(b'> ')
            self.remote.sendline(b'0')
            self.close()

            return True

        return False

    def register(self, username: bytes, password: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(b'1')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(username)

        if b'[ERROR]' in self.remote.recvline():
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(password)

        if b'[ERROR]' in self.remote.recvline():
            self.close()
            return False

        return True

    def login(self, username: bytes, password: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(b'2')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(username)

        if b'[ERROR]' in self.remote.recvline(): # invalid or not found
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(password)

        if b'[ERROR]' in self.remote.recvline(): # invalid or wrong
            self.close()
            return False

        return True

    def create_playlist(self, name: bytes, description: bytes, num_songs: int, songs: list[bytes]) -> bool:
        if not self.connected:
            return False

        assert len(songs) == num_songs, 'ayo check you bastard'

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        if b'[ERROR]' in self.remote.recvline(): # duplicate or invalid
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(description)

        if b'[ERROR]' in self.remote.recvline(): # invalid
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(str(num_songs).encode())

        if b'[ERROR]' in self.remote.recvline(): # invalid
            self.close()
            return False

        for song in songs:
            self.remote.recvuntil(b': ')
            self.remote.sendline(song)

            if self.remote.recvn(4) != b'Song': # invalid
                self.close()
                return False

        return b'[ERROR]' not in self.remote.recvline()

    def inspect_playlists(self) -> dict | bool:
        if not self.connected:
            return False

        first7 = self.remote.recvn(7)

        if first7 == b'[ERROR]': # path or read issue
            self.close()
            return False

        res = dict()

        while b': ' in (line := self.remote.recvline()):
            name = line.split(b': ')[-1].strip()
            desc = self.remote.recvline().replace(b'"', b'').strip()

            res[name] = (desc, [])

            while b'Song' == (line := self.remote.recvn(4)):
                song = line.split(b': ')[-1].strip()

                res[name] = (desc, res[name][1] + [song])

        return res

    def play_random_song(self) -> bool:
        if not self.connected:
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(b'3')

        return b'Select' not in self.remote.recvline()

    def create_artist(self, name: bytes, description: bytes, key: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(b'4')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        if b'[ERROR]' in self.remote.recvline():
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(description)

        if b'[ERROR]' in self.remote.recvline():
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(key)

        if b'[ERROR]' in self.remote.recvline():
            self.close()
            return False

        return True

    def decrypt_artist(self, name: bytes, key: bytes) -> bool | bytes:
        if not self.connected:
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(b'5')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        if b'[ERROR]' in self.remote.recvline():
            self.close()
            return False

        self.remote.recvuntil(b'> ')
        self.remote.sendline(key)

        if b'[ERROR]' == (line := self.remote.recvline())[:7]:
            self.close()
            return False

        desc = line.split(b'"')[1]

        return desc
