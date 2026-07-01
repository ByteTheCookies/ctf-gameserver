#!/usr/bin/env python3
import random
import string
import json
import logging
import traceback
from functools import partial
from checklib import *
from client import Client
from ctf_gameserver import checkerlib

PORT = 2345
ALPHABET = string.ascii_letters + string.digits

def rand_str(length):
    return ''.join(random.choices(ALPHABET, k=length))

def check_register(host):
    u, p = rand_str(10).encode(), rand_str(10).encode()
    client = Client(host, PORT)
    client.connect()
    client.sync()
    res = client.register(u, p)
    client.close()
    return res, (u, p)

def check_login(host):
    u, p = rand_str(10).encode(), rand_str(10).encode()
    client = Client(host, PORT)
    client.connect()
    client.sync()
    assert client.register(u, p)
    res = client.login(u, p)
    client.close()
    return res, (u, p)

def check_banking(host):
    u1, p1 = rand_str(10).encode(), rand_str(10).encode()
    u2, p2 = rand_str(10).encode(), rand_str(10).encode()

    client = Client(host, PORT)
    client.connect()
    client.sync()

    assert client.register(u1, p1)
    assert client.register(u2, p2)
    assert client.login(u1, p1)

    assert client.deposit(b't1', b'd1', 50)
    assert client.withdraw(b't2', b'd2', 10)
    assert client.gift(u2, b't3', b'd3', 20)

    txs = client.my_transactions()
    assert txs and len(txs) == 3
    assert txs[-1]['title'] == 't3'

    pub_txs = client.user_transactions(u1)
    assert pub_txs and 'pub' in pub_txs and len(pub_txs['txs']) == 3

    client.close()
    return True, (u1, u2)

def check_sla(host):
    utils = [
        partial(check_register, host),
        partial(check_login, host),
        partial(check_banking, host)
    ]
    messages = {
        "check_register": "Registration failed",
        "check_login": "Login failed",
        "check_banking": "Core banking flow failed"
    }

    for u in utils:
        try:
            check, data = u()
            if not check:
                quit(Status.DOWN, messages[u.func.__name__], str(data))
        except Exception:
            quit(Status.DOWN, messages[u.func.__name__], str(traceback.format_exc()))

    quit(Status.OK, 'OK')

def put_flag(host, flag):
    try:
        random.seed(flag.encode())
        u = rand_str(16)
        p = rand_str(16)
        title = b'secret'
        desc = flag.encode()

        client = Client(host, PORT)
        client.connect()
        client.sync()

        assert client.register(u.encode(), p.encode())
        assert client.login(u.encode(), p.encode())
        assert client.deposit(title, desc, 1)
        client.close()

        return {"username": u}

    except Exception:
        client.close()
        quit(Status.DOWN, "Cannot put flag", str(traceback.format_exc()) + f"\n{flag}")

def get_flag(host, flag):
    random.seed(flag.encode())
    u = rand_str(16)
    p = rand_str(16)

    client = Client(host, PORT)
    client.connect()
    client.sync()

    if not client.login(u.encode(), p.encode()):
        client.close()
        quit(Status.DOWN, "Cannot get flag", f"{flag}")

    txs = client.my_transactions()
    client.close()

    if not txs:
        return False

    for tx in txs:
        if tx.get("description") == flag:
            return True

    return False

def _map_legacy_system_exit(exc: SystemExit) -> checkerlib.CheckResult:
    try:
        code = int(exc.code)
    except Exception:
        code = Status.ERROR.value

    if code == Status.OK.value:
        return checkerlib.CheckResult.OK
    if code == Status.DOWN.value:
        return checkerlib.CheckResult.DOWN
    return checkerlib.CheckResult.FAULTY

class Swink1Checker(checkerlib.BaseChecker):
    def place_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        try:
            flag_id = put_flag(self.ip, flag)
            checkerlib.set_flagid(json.dumps(flag_id))
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:
            logging.exception("swink place_flag failed")
            return checkerlib.CheckResult.DOWN

    def check_service(self):
        try:
            check_sla(self.ip)
            return checkerlib.CheckResult.OK
        except SystemExit as exc:
            return _map_legacy_system_exit(exc)
        except Exception:
            logging.exception("swink check_service failed")
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
        except Exception:
            logging.exception("swink check_flag failed")
            return checkerlib.CheckResult.DOWN

if __name__ == '__main__':
    checkerlib.run_check(Swink1Checker)
