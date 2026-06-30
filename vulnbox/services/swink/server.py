#!/usr/bin/env python3

import sqlite3
import hashlib
import json
import crypto  # ponytail: expects generate() -> (priv, pub), sign(msg, priv) -> str, encrypt(msg, priv) -> str, decrypt(c, priv) -> str

DB_FILE = "bank.db"

def initialize_database():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, pub TEXT, priv TEXT, balance INTEGER)")
        conn.execute("CREATE TABLE IF NOT EXISTS transactions (username TEXT, title TEXT, description TEXT, amount INTEGER, signature TEXT)")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

def record_transaction(username, title, description, amount):
    with sqlite3.connect(DB_FILE) as conn:
        user = conn.execute("SELECT priv, balance FROM users WHERE username = ?", (username,)).fetchone()
        conn.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))

        # ponytail: signing the plaintext so the signature remains valid for the underlying action
        msg = f"{title}|{description}|{amount}"
        sig = crypto.sign(msg, int(user[0], 16))

        enc_title = crypto.encrypt(title, int(user[0], 16))
        enc_desc = crypto.encrypt(description, int(user[0], 16))

        conn.execute("INSERT INTO transactions (username, title, description, amount, signature) VALUES (?, ?, ?, ?, ?)",
                     (username, enc_title, enc_desc, amount, sig))

def get_transactions(username):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT title, description, amount, signature FROM transactions WHERE username = ?", (username,)).fetchall()
        return [dict(r) for r in rows]

def serve():
    initialize_database()
    current_user = None

    menu = """
1) Register
2) Login
3) Logout
4) Deposit
5) Withdraw
6) Gift
7) My Transactions
8) User Transactions
9) Exit
"""

    while True:
        try:
            print(f"\n[{current_user or 'guest'}]" + menu)
            cmd = input("Choice: ").strip()

            if cmd == "1":
                u, p = input("username: "), input("password: ")
                if get_user(u):
                    print("err: user exists")
                else:
                    priv, pub = crypto.generate()
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (u, hash_password(p), hex(pub), hex(priv), 100))
                    print("ok")

            elif cmd == "2":
                u, p = input("username: "), input("password: ")
                user_data = get_user(u)
                if user_data and user_data["password"] == hash_password(p):
                    current_user = u
                    print("ok")
                else:
                    print("err: invalid credentials")

            elif cmd == "3":
                current_user = None
                print("ok")

            elif cmd in ("4", "5"):
                if not current_user:
                    print("err: log in first")
                    continue

                t, desc = input("title: "), input("description: ")
                amt = int(input("amount: "))

                if amt <= 0:
                    print("err: amount must be positive")
                    continue
                elif amt >= 2**16:
                    print(f"err: amount must be at most {2**16 - 1}")
                    continue
                if cmd == "5" and get_user(current_user)["balance"] < amt:
                    print("err: insufficient funds")
                    continue

                record_transaction(current_user, t, desc, amt if cmd == "4" else -amt)
                print("ok")

            elif cmd == "6":
                if not current_user:
                    print("err: log in first")
                    continue

                target = input("to (username): ")
                t, desc = input("title: "), input("description: ")
                amt = int(input("amount: "))

                if amt <= 0 or not get_user(target) or get_user(current_user)["balance"] < amt:
                    print("err: invalid target, amount, or insufficient funds")
                    continue

                record_transaction(current_user, t, desc, -amt)
                record_transaction(target, t, desc, amt)
                print("ok")

            elif cmd == "7":
                if not current_user:
                    print("err: log in first")
                    continue

                txs = get_transactions(current_user)
                priv = int(get_user(current_user)["priv"], 16)
                for tx in txs:
                    try:
                        tx["title"] = crypto.decrypt(tx["title"], priv)
                        tx["description"] = crypto.decrypt(tx["description"], priv)
                    except Exception:
                        pass # ponytail: fallback if decryption fails
                print(json.dumps(txs, indent=2))

            elif cmd == "8":
                target = input("username: ")
                user_data = get_user(target)
                if user_data:
                    # ponytail: prints raw txs (which are now encrypted text for title/desc)
                    print(json.dumps({"pub": user_data["pub"], "txs": get_transactions(target)}, indent=2))
                else:
                    print("err: user not found")
            else:
                break

        except EOFError:
            break
        except ValueError:
            print("err: invalid number format")
        except Exception as e:
            print(e)
            # ponytail: blanket catch to keep ncat alive on fuzzed/bad inputs.
            print("err: unexpected error")

if __name__ == "__main__":
    serve()

