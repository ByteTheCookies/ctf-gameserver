#!/usr/bin/env python3

from checklib import *
import random
import string
from client import Client
import traceback

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

    client = Client(host, port)

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

    client = Client(host, port)

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

    client = Client(host, port)

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

    # Post flag id to game server
    try:
        post_flag_id('vulnify-2', team_id, flag_id)
    except Exception:
        quit(Status.ERROR, 'Failed to post flag id', str(traceback.format_exc()) + f"\n{flag}")

    quit(Status.OK, 'OK')


def get_flag(host, flag):
    random.seed(flag.encode())

    username = rand_str(random.randint(10, 30))
    password = rand_str(random.randint(1, 30))
    artist = rand_str(random.randint(5, 25))
    key = rand_str(random.randint(5, 15))

    client = Client(host, PORT)

    if not client.register(username.encode(), password.encode()):
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    if not client.login(username.encode(), password.encode()):
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    recovered = client.decrypt_artist(artist, key)

    if recovered != flag:
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    quit(Status.OK, 'OK')


if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'
    if 'LOCALHOST' in os.environ:
        host = '127.0.0.1'

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception:
            quit(Status.DOWN, 'Cannot check SLA', str(traceback.format_exc()))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot put flag", str(traceback.format_exc()))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot get flag", str(traceback.format_exc()))
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK)
