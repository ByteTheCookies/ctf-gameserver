#!/usr/bin/env python3

from ctf_gameserver import checkerlib
from pwn import *
import pwnlib
import string
import logging
import re
import random

from utils import CakeOrder

pwnlib.tubes.remote.log.setLevel(logging.WARN)
context.timeout = 10
PORT = 4321
ALPHABET = string.digits+string.ascii_letters

class TemplateChecker(checkerlib.BaseChecker):
    _process = None

    def enter_raw(self, data):
        self._process.send(data.encode() + b"\x0d")

    def enter(self, data):
        self._process.send(data.encode() + b"\x0d")
        response = self._process.recvuntil(b"EOP"*14, timeout=10).decode()
        if response=="":
            raise TimeoutError
        return response

    def multitab(self, data_arr):
        payload = "".join([data+"\x09" for data in data_arr]).encode()
        self._process.send(payload)

    def tab(self, data):
        self._process.send(data.encode() + b"\x09")

    def random_creds(self):
        uname = "".join([random.choice(ALPHABET) for i in range(random.choice(range(8,17)))])
        pw = "".join([random.choice(ALPHABET) for i in range(random.choice(range(8,17)))])
        return (uname, pw)

    def set_new_conn(self):
        if self._process is not None:
            self.enter_raw("M")
            self.enter_raw("Q")
            self._process.close()
        self._process = remote(self.ip, PORT)
        response = self._process.recvuntil(b"EOP"*14, timeout=10).decode()
        if response=="":
            raise TimeoutError
        self.enter("C")
    
    def register_user(self, uname, pw):
        logging.info(f"Registering user: {uname=}, {pw=}")
        self.enter("R")
        self.tab(uname)
        self.tab(pw)
        res = self.enter("C")
        if not f"Registration successful" in res:
            logging.error(f"Login failed with {uname=}")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        return True
    
    def login_user(self, uname, pw):
        logging.info(f"Logging in user: {uname=}, {pw=}")
        self.enter("L")
        self.tab(uname)
        self.tab(pw)
        res = self.enter("C")
        if not f"login successful" in res:
            logging.error(f"Login failed with {uname=}")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        return True

    def create_order_base(self, cakeOrder):
        logging.info(f"Creating {cakeOrder}")
        self.enter("O")
        self.multitab([cakeOrder.size, cakeOrder.flavor, cakeOrder.toppings, cakeOrder.customtxt, cakeOrder.comment])
        res = self.enter("C")
        return res
        
    def create_order(self, cakeOrder):
        res = self.create_order_base(cakeOrder)
        if not cakeOrder.flavor in res:
            logging.error(f"Failed creating order: {cakeOrder}")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        else:
            return True

    def create_order_get_tid(self, cakeOrder):
        res = self.create_order_base(cakeOrder)
        match = re.search(r"Tracking-ID:.*?([A-Z0-9]{16})", res)
        if not match:
            logging.error("Couldnt extract Tracking-ID, order creation failed?")
            logging.error("Received data:");
            logging.error(res.encode());
            return (False, None)
        tid = match.group(1)
        if not cakeOrder.flavor in res:
            logging.error(f"Failed creating order: {cakeOrder}")
            logging.error("Received data:");
            logging.error(res.encode());
            return (False, tid)
        return (True, tid)
        
    def track_order(self, tid):
        self.enter("T")
        return self.enter(tid)

    def check_user_generation(self):
        self.set_new_conn()
        (uname, pw) = self.random_creds()
        logging.info(f"User Generation check with {uname=}")
        if not self.register_user(uname, pw):
            return False
        if not self.login_user(uname, pw):
            return False
        logging.info(f"User Generation Check with {uname=} successful")
        return True
    
    def check_order_generation(self):
        self.set_new_conn()
        (uname, pw) = self.random_creds()
        logging.info(f"Order Generation check with {uname=}")
        if not self.register_user(uname, pw):
            return False
        if not self.login_user(uname, pw):
            return False
        cakeOrder = CakeOrder()
        if not self.create_order(cakeOrder):
            return False
        logging.info(f"User Generation Check with {uname=} successful")
        return True

    def check_order_overview(self):
        self.set_new_conn()
        (uname, pw) = self.random_creds()
        logging.info(f"Order Overview check with {uname=}")
        if not self.register_user(uname, pw):
            return False
        if not self.login_user(uname, pw):
            return False
        cakeOrder = CakeOrder()
        if not self.create_order(cakeOrder):
            return False
        self.enter("M")
        res = self.enter("V")
        if not cakeOrder.flavor in res:
            logging.error("Couldnt find cake order in order overview")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        logging.info(f"Order Overview Check with {uname=} successful")
        return True

    def check_order_tracking_loggedin(self):
        self.set_new_conn()
        (uname, pw) = self.random_creds()
        logging.info(f"Tracking check[loggedin] with {uname=}")
        if not self.register_user(uname, pw):
            return False
        if not self.login_user(uname, pw):
            return False
        cakeOrder = CakeOrder()
        (res, tid) = self.create_order_get_tid(cakeOrder)
        if not res:
            return False
        res = self.track_order(tid)
        if cakeOrder.flavor not in res:
            logging.error("Order msg not found via tracking id")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        logging.info(f"Tracking check[loggedin] with {uname=} successful")
        return True

    
    def check_order_tracking_loggedout(self):
        self.set_new_conn()
        (uname, pw) = self.random_creds()
        logging.info(f"Tracking check[loggedout]")
        if not self.register_user(uname, pw):
            return False
        if not self.login_user(uname, pw):
            return False
        cakeOrder = CakeOrder()
        (res, tid) = self.create_order_get_tid(cakeOrder)
        if not res:
            return False
        self.set_new_conn() # new conn -> loggedout
        res = self.track_order(tid)
        if cakeOrder.flavor not in res:
            logging.error("Order msg not found via tracking id")
            logging.error("Received data:");
            logging.error(res.encode());
            return False
        logging.info(f"Tracking check[loggedout] successful")
        return True

    def place_flag(self, tick):
        try:
            flag = checkerlib.get_flag(tick)
            self.set_new_conn()
            (uname, pw) = self.random_creds()
            self.register_user(uname, pw)
            if not self.login_user(uname, pw):
                return checkerlib.CheckResult.FAULTY
            cakeOrder = CakeOrder()
            cakeOrder.use_flag(flag)
            (suc, tid) = self.create_order_get_tid(cakeOrder)
            if not suc:
                return checkerlib.CheckResult.FAULTY
            logging.info(f"Successfully placed flag with {tid=}")
            checkerlib.store_state(str(tick), {"flag": flag, "uname": uname, "pw": pw, "tid": tid})
            uid = tid[:4]
            checkerlib.set_flagid(f"{uname=}, {uid=}")
        except PwnlibException:
            return checkerlib.CheckResult.DOWN
        return checkerlib.CheckResult.OK

    def check_service(self):
        checks = [
            self.check_user_generation,
            self.check_order_generation,
            self.check_order_tracking_loggedin,
            self.check_order_tracking_loggedout,
            self.check_order_overview
        ]
        random.shuffle(checks)
        try:
            for check in checks:
                if not check():
                    return checkerlib.CheckResult.FAULTY
        except PwnlibException:
            pass
        return checkerlib.CheckResult.OK

    def check_flag(self, tick):
        try:
            state = checkerlib.load_state(str(tick))
            if state is None:
                logging.error(f"Unable to load state of tick {tick}")
                return checkerlib.CheckResult.FLAG_NOT_FOUND
            tid = state["tid"]
            self.set_new_conn()
            res = self.track_order(tid)
            if state["flag"] not in res:
                logging.error(f"Couldnt find {state["flag"]=} with {tid=}")
                logging.error("Received data:");
                logging.error(res.encode());
                return checkerlib.CheckResult.FLAG_NOT_FOUND
        except PwnlibException:
            return checkerlib.CheckResult.DOWN
        return checkerlib.CheckResult.OK

if __name__ == '__main__':
    checkerlib.run_check(TemplateChecker)
