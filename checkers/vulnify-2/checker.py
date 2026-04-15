#!/usr/bin/env python3

from checklib import *
import random
import string
import json
import logging
from client import Client
import traceback
from ctf_gameserver import checkerlib

PORT = 1337
ALPHABET = string.ascii_letters + string.digits


def rand_str(length):
    return ''.join(random.choices(ALPHABET, k=length))

def check_register():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()

    client = Client(host, PORT)

    return client.register(username, password), (username, password)

def check_login():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()

    client = Client(host, PORT)

    # shouldn't fail because check_register is done first
    client.register(username, password)

    return client.login(username, password), (username, password)

def check_create_playlist():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()

    pl_name = rand_str(random.randint(10, 20)).encode()
    pl_desc = rand_str(random.randint(10, 20)).encode()
    num_songs = random.randint(1, 23)
    songs = [rand_str(random.randint(2, 10)).encode() for _ in range(num_songs)]

    client = Client(host, PORT)

    client.register(username, password)
    client.login(username, password), (username, password)

    return client.create_playlist(pl_name, pl_desc, num_songs, songs), (pl_name, pl_desc, num_songs, songs)

def check_inspect_playlists():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()

    pl_name = rand_str(random.randint(10, 20)).encode()
    pl_desc = rand_str(random.randint(10, 20)).encode()
    num_songs = random.randint(1, 23)
    songs = [rand_str(random.randint(2, 10)).encode() for _ in range(num_songs)]

    client = Client(host, PORT)

    client.register(username, password)
    client.login(username, password), (username, password)
    client.create_playlist(pl_name, pl_desc, num_songs, songs), (pl_name, pl_desc, num_songs, songs)

    res = client.inspect_playlists()

    if not res or len(res) > 1:
        return False, (pl_name, pl_desc, num_songs, songs)

    try:
        desc, sgs = res[pl_name]

        assert desc == pl_desc and sgs == songs

        return True, (pl_name, pl_desc, num_songs, songs)
    except:
        return False, (pl_name, pl_desc, num_songs, songs)

def check_play_random_song():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()

    client = Client(host, PORT)

    return client.play_random_song(), (username, password)

def check_create_artist():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()
    artist = rand_str(random.randint(5, 30)).encode()
    description = rand_str(random.randint(10, 60)).encode()
    key = rand_str(random.randint(5, 15)).encode()

    client = Client(host, PORT)

    return client.create_artist(artist, description, key), (artist, description, key)

def check_decrypt_artist():
    username = rand_str(random.randint(5, 20)).encode()
    password = rand_str(random.randint(5, 20)).encode()
    artist = rand_str(random.randint(5, 30)).encode()
    description = rand_str(random.randint(10, 60)).encode()
    key = rand_str(random.randint(5, 15)).encode()

    client = Client(host, PORT)

    client.create_artist(artist, description, key)

    return client.decrypt_artist(artist, key) == description, (artist, key)


def check_sla(host):
    # Check service functionality
    utils = [
        check_register,
        check_login,
        check_create_playlist,
        check_inspect_playlists,
        check_play_random_song,
        check_create_artist,
        check_decrypt_artist
        ]

    messages = {
        "check_register": "Registration failed",
        "check_login": "Login failed",
        "check_create_playlist": "Create playlist failed",
        "check_inspect_playlists": "Inspect playlists failed",
        "check_play_random_song": "Play random song failed",
        "check_create_artist": "Create artist failed",
        "check_decrypt_artist": "Decrypt artist failed",
    }
 
    for u in utils:
        try:
            check, data = u()
            if not check:
                quit(Status.DOWN, messages[u.__name__], str(data))
        except Exception:
            quit(Status.DOWN, messages[u.__name__], str(traceback.format_exc()))

    quit(Status.OK, 'OK')


def put_flag(host, flag):
    try:
        random.seed(flag.encode())

        username = rand_str(random.randint(10, 30))
        password = rand_str(random.randint(10, 30))
        artist = rand_str(random.randint(5, 25))
        key = rand_str(random.randint(5, 15))

        flag_id = {"username": username, "artist": artist}

        client = Client(host, PORT)
        client.connect()

        assert client.register(username.encode(), password.encode())

        assert client.login(username.encode(), password.encode())

        assert client.create_artist(artist.encode(), flag.encode(), key.encode())

        assert client.exit()

    except Exception:
            quit(Status.DOWN, "Cannot set flag", str(traceback.format_exc()) + f"\n{flag}")

    return flag_id


def get_flag(host, flag):
    random.seed(flag.encode())

    username = rand_str(random.randint(10, 30))
    password = rand_str(random.randint(10, 30))
    artist = rand_str(random.randint(5, 25))
    key = rand_str(random.randint(5, 15))

    client = Client(host, PORT)

    if not client.register(username.encode(), password.encode()):
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    if not client.login(username.encode(), password.encode()):
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    recovered = client.decrypt_artist(artist, key)

    if recovered != flag:
        return False
    return True


def _map_legacy_system_exit(exc: SystemExit) -> checkerlib.CheckResult:
    try:
        code = int(exc.code)
    except Exception:  # noqa: BLE001
        code = Status.ERROR.value

    if code == Status.OK.value:
        return checkerlib.CheckResult.OK
    if code == Status.DOWN.value:
        return checkerlib.CheckResult.DOWN
    return checkerlib.CheckResult.FAULTY


class Vulnify2Checker(checkerlib.BaseChecker):
    def place_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        try:
            flag_id = put_flag(self.ip, flag)
            checkerlib.set_flagid(json.dumps(flag_id))
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:  # noqa: BLE001
            logging.exception("vulnify-2 place_flag failed")
            return checkerlib.CheckResult.DOWN

    def check_service(self):
        try:
            check_sla(self.ip)
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:  # noqa: BLE001
            logging.exception("vulnify-2 check_service failed")
            return checkerlib.CheckResult.DOWN

    def check_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        try:
            if get_flag(self.ip, flag):
                return checkerlib.CheckResult.OK
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        except SystemExit as exc:
            result = _map_legacy_system_exit(exc)
            if result == checkerlib.CheckResult.DOWN:
                return checkerlib.CheckResult.FLAG_NOT_FOUND
            return result
        except Exception:  # noqa: BLE001
            logging.exception("vulnify-2 check_flag failed")
            return checkerlib.CheckResult.DOWN


if __name__ == '__main__':
    checkerlib.run_check(Vulnify2Checker)
