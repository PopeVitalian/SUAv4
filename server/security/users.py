import hashlib
import json
import os

# users.json živi v korenu projekta (ne glede na delovni imenik procesa)
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "users.json")

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def register(username, password, role):
    users = _load_users()
    
    if username in users:
        raise ValueError("Username already exists")
    elif role not in ("writer", "reader"):
        raise ValueError("Role not writer or reader")

    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)

    users[username] = {"salt": salt.hex(), "hash": password_hash.hex(), "role": role}
    _save_users(users)
    return {"username": username, "role": role}

def verify(username, password):
    users = _load_users()
    
    if username not in users:
        stored_salt = os.urandom(16)
        stored_hash = "0" * 64          # dummy: can never match
    else:
        stored_salt = bytes.fromhex(users[username]["salt"])
        stored_hash = users[username]["hash"]

    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), stored_salt, 200_000)

    if new_hash.hex() == stored_hash:
        return users[username]["role"]

    return None
    