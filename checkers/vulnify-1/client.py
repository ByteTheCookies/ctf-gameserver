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

    def sync(self):
        if self.connected:
            self.remote.recvuntil(b'> ', timeout=5)

    def register(self, username: bytes, password: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.sendline(b'1')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(username)

        try:
            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(password)

            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return True

    def login(self, username: bytes, password: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.sendline(b'2')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(username)

        try:
            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(password)

            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return True

    def create_playlist(self, name: bytes, description: bytes, num_songs: int, songs: list[bytes]) -> bool:
        if not self.connected:
            return False

        assert len(songs) == num_songs, 'ayo check you bastard'

        self.remote.sendline(b'1')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        try:
            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(description)

            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(str(num_songs).encode())

            try:
                for song in songs:
                    self.remote.recvuntil(b': ', timeout=5)
                    self.remote.sendline(song)
            except:
                self.close()
                return False

            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return True

    def inspect_playlists(self) -> dict | bool:
        if not self.connected:
            return False

        self.remote.sendline(b'2')

        try:
            blob = self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        if b'[ERROR]' in blob:
            return False

        if b'Select an option' in blob:
            blob = blob.split(b'Select an option')[0]

        res = {}

        parts = blob.split(b'Playlist: ')
        for part in parts[1:]:
            lines = part.splitlines()
            if len(lines) < 2:
                continue

            name = lines[0].strip()
            desc = lines[1].replace(b'"', b'').strip()

            songs = []
            for ln in lines[2:]:
                if ln.startswith(b'\tSong'):
                    songs.append(ln.split(b': ', 1)[-1].strip())

            res[name] = (desc, songs)

        return res

    def play_random_song(self) -> bool:
        if not self.connected:
            return False

        self.remote.sendline(b'3')

        try:
            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return True

    def create_artist(self, name: bytes, description: bytes, key: bytes) -> bool:
        if not self.connected:
            return False

        self.remote.sendline(b'4')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        try:
            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(description)

            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(key)

            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return True

    def decrypt_artist(self, name: bytes, key: bytes) -> bool | bytes:
        if not self.connected:
            return False

        self.remote.sendline(b'5')

        self.remote.recvuntil(b'> ')
        self.remote.sendline(name)

        try:
            self.remote.recvuntil(b'> ', timeout=5)
            self.remote.sendline(key)

            self.remote.recvuntil(b':\n', timeout=5)
            desc = self.remote.recvline().strip()

            self.remote.recvuntil(b'> ', timeout=5)
        except:
            self.close()
            return False

        return desc
