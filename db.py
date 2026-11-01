"""SQLite data layer: users, predictions, settings and audit log.

Passwords are never stored in plain text: PBKDF2-HMAC-SHA256 with a random salt per user.
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import pandas as pd

DATA_DIR = os.environ.get("MALARIA_DATA_DIR", "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")
ITERATIONS = 200_000
MAX_FAILS = 5
LOCK_SECONDS = 300
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "Admin@12345"  # sirf fallback: secrets set na hon to. App warning dikhata hai.
RESERVED = {"admin", "administrator", "root", "support", "system", "guest", "moderator"}

DEFAULT_SETTINGS = {
    "signups_enabled": "1",
    "maintenance": "0",
    "announcement_on": "0",
    "announcement": "",
    "conf_warn": "0.70",
    "log_guest": "1",
    "timezone": "Asia/Karachi",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  full_name TEXT DEFAULT '',
  pw_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  last_login TEXT,
  failed_count INTEGER NOT NULL DEFAULT 0,
  locked_until REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS predictions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  username TEXT NOT NULL,
  source TEXT NOT NULL,
  filename TEXT,
  label TEXT NOT NULL,
  confidence REAL NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_pred_user ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_pred_time ON predictions(created_at);
"""

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,24}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_ADMIN_CREDS = (None, None)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def _db():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _one(sql, params=()):
    with _db() as c:
        r = c.execute(sql, params).fetchone()
        return dict(r) if r else None


def _hash(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS).hex()


def _verify(password, salt_hex, stored):
    return hmac.compare_digest(_hash(password, salt_hex), stored)


def _public(r):
    return {k: r[k] for k in ("id", "username", "email", "full_name", "role", "status", "created_at", "last_login")}


def password_problem(pw):
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return "Password needs letters and at least one number."
    return None


# ----------------------------------------------------------------- setup
def init_db(admin_user=None, admin_pass=None):
    global _ADMIN_CREDS
    _ADMIN_CREDS = (admin_user, admin_pass)
    with _db() as c:
        c.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    custom = bool(admin_user and admin_pass)
    u = admin_user if custom else DEFAULT_ADMIN_USER
    p = admin_pass if custom else DEFAULT_ADMIN_PASS
    row = _one("SELECT * FROM users WHERE username=?", (u,))
    if row is None:
        _insert(u, f"{u.lower()}@admin.local", p, "Administrator", "admin")
        audit("system", "admin_seeded", u)
    elif custom and not _verify(p, row["salt"], row["pw_hash"]):
        salt = secrets.token_hex(16)
        with _db() as c:
            c.execute("UPDATE users SET pw_hash=?, salt=?, role='admin', status='active', failed_count=0, locked_until=0 WHERE id=?",
                      (_hash(p, salt), salt, row["id"]))
        audit("system", "admin_password_synced_from_secrets", u)


def default_admin_in_use():
    r = _one("SELECT * FROM users WHERE username=? AND role='admin'", (DEFAULT_ADMIN_USER,))
    return bool(r and _verify(DEFAULT_ADMIN_PASS, r["salt"], r["pw_hash"]))


def _insert(username, email, password, full_name, role):
    salt = secrets.token_hex(16)
    with _db() as c:
        cur = c.execute(
            "INSERT INTO users(username,email,full_name,pw_hash,salt,role,created_at) VALUES(?,?,?,?,?,?,?)",
            (username, email, full_name, _hash(password, salt), salt, role, _now()))
        return cur.lastrowid


# ------------------------------------------------------------- settings
def get_settings():
    with _db() as c:
        d = dict(DEFAULT_SETTINGS)
        d.update({r["key"]: r["value"] for r in c.execute("SELECT key,value FROM settings")})
    return d


def get_setting(key):
    return get_settings().get(key, "")


def set_setting(key, value):
    with _db() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, str(value)))


# ----------------------------------------------------------------- audit
def audit(actor, action, detail=""):
    with _db() as c:
        c.execute("INSERT INTO audit(ts,actor,action,detail) VALUES(?,?,?,?)", (_now(), actor, action, detail))


def audit_df(limit=3000):
    with _db() as c:
        return pd.read_sql_query("SELECT ts, actor, action, detail FROM audit ORDER BY id DESC LIMIT ?", c, params=(limit,))


# ----------------------------------------------------------------- users
def create_user(username, email, password, full_name=""):
    username, email, full_name = username.strip(), email.strip(), full_name.strip()
    if not USERNAME_RE.match(username):
        return False, "Username must be 3-24 characters: letters, numbers, dot or underscore.", None
    if username.lower() in RESERVED:
        return False, "That username is reserved. Please choose another.", None
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address.", None
    problem = password_problem(password)
    if problem:
        return False, problem, None
    try:
        uid = _insert(username, email, password, full_name, "user")
    except sqlite3.IntegrityError:
        return False, "That username or email is already registered.", None
    audit(username, "signup", email)
    return True, "Account created.", uid


def authenticate(identifier, password):
    identifier = identifier.strip()
    r = _one("SELECT * FROM users WHERE username=? OR email=?", (identifier, identifier))
    generic = "Invalid username or password."
    if r is None:
        _hash(password, "00" * 16)  # same time cost, so usernames cannot be guessed by timing
        return None, generic
    if r["locked_until"] and r["locked_until"] > time.time():
        mins = int((r["locked_until"] - time.time()) // 60) + 1
        return None, f"Too many failed attempts. Try again in about {mins} min."
    if not _verify(password, r["salt"], r["pw_hash"]):
        fails = r["failed_count"] + 1
        lock = time.time() + LOCK_SECONDS if fails >= MAX_FAILS else 0
        with _db() as c:
            c.execute("UPDATE users SET failed_count=?, locked_until=? WHERE id=?", (0 if lock else fails, lock, r["id"]))
        if lock:
            audit(r["username"], "account_locked", "too many failed logins")
        return None, generic
    if r["status"] != "active":
        return None, "This account is suspended. Contact the administrator."
    with _db() as c:
        c.execute("UPDATE users SET failed_count=0, locked_until=0, last_login=? WHERE id=?", (_now(), r["id"]))
    audit(r["username"], "login", "")
    return _public(_one("SELECT * FROM users WHERE id=?", (r["id"],))), "ok"


def get_user(uid):
    r = _one("SELECT * FROM users WHERE id=?", (uid,))
    return _public(r) if r else None


def get_user_by_name(username):
    r = _one("SELECT * FROM users WHERE username=?", (username,))
    return _public(r) if r else None


def users_df():
    with _db() as c:
        return pd.read_sql_query(
            "SELECT id, username, full_name, email, role, status, created_at, last_login FROM users ORDER BY id", c)


def _active_admins():
    with _db() as c:
        return c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND status='active'").fetchone()[0]


def _would_remove_last_admin(uid):
    u = get_user(uid)
    return bool(u and u["role"] == "admin" and u["status"] == "active" and _active_admins() <= 1)


def set_role(uid, role, actor):
    if role not in ("user", "admin"):
        return False, "Invalid role."
    if role == "user" and _would_remove_last_admin(uid):
        return False, "You cannot remove the last active admin."
    with _db() as c:
        c.execute("UPDATE users SET role=? WHERE id=?", (role, uid))
    audit(actor, "role_changed", f"user#{uid} -> {role}")
    return True, "Role updated."


def set_status(uid, status, actor):
    if status not in ("active", "suspended"):
        return False, "Invalid status."
    if status == "suspended" and _would_remove_last_admin(uid):
        return False, "You cannot suspend the last active admin."
    with _db() as c:
        c.execute("UPDATE users SET status=?, failed_count=0, locked_until=0 WHERE id=?", (status, uid))
    audit(actor, "status_changed", f"user#{uid} -> {status}")
    return True, "Status updated."


def reset_password(uid, new_password, actor):
    problem = password_problem(new_password)
    if problem:
        return False, problem
    salt = secrets.token_hex(16)
    with _db() as c:
        c.execute("UPDATE users SET pw_hash=?, salt=?, failed_count=0, locked_until=0 WHERE id=?",
                  (_hash(new_password, salt), salt, uid))
    audit(actor, "password_reset", f"user#{uid}")
    return True, "Password updated."


def change_password(uid, old, new):
    r = _one("SELECT * FROM users WHERE id=?", (uid,))
    if not r or not _verify(old, r["salt"], r["pw_hash"]):
        return False, "Current password is incorrect."
    ok, msg = reset_password(uid, new, r["username"])
    return ok, ("Password changed." if ok else msg)


def update_profile(uid, full_name, email):
    email = email.strip()
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    try:
        with _db() as c:
            c.execute("UPDATE users SET full_name=?, email=? WHERE id=?", (full_name.strip(), email, uid))
    except sqlite3.IntegrityError:
        return False, "That email is already used by another account."
    return True, "Profile updated."


def delete_user(uid, actor, password=None):
    u = _one("SELECT * FROM users WHERE id=?", (uid,))
    if not u:
        return False, "User not found."
    if _would_remove_last_admin(uid):
        return False, "You cannot delete the last active admin."
    if password is not None and not _verify(password, u["salt"], u["pw_hash"]):
        return False, "Password is incorrect."
    with _db() as c:
        c.execute("DELETE FROM predictions WHERE user_id=?", (uid,))
        c.execute("DELETE FROM users WHERE id=?", (uid,))
    audit(actor, "user_deleted", u["username"])
    return True, "Account deleted."


# ----------------------------------------------------------- predictions
def log_prediction(user_id, username, source, filename, label, confidence):
    with _db() as c:
        c.execute("INSERT INTO predictions(user_id,username,source,filename,label,confidence,created_at) VALUES(?,?,?,?,?,?,?)",
                  (user_id, username, source, filename, label, float(confidence), _now()))


def predictions_df(user_id=None, limit=20000):
    q = "SELECT id, user_id, username, source, filename, label, confidence, created_at FROM predictions"
    params = []
    if user_id is not None:
        q += " WHERE user_id=?"
        params.append(user_id)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with _db() as c:
        return pd.read_sql_query(q, c, params=params)


def delete_predictions(user_id=None, older_than_days=None, actor="system"):
    with _db() as c:
        if user_id is not None:
            n = c.execute("DELETE FROM predictions WHERE user_id=?", (user_id,)).rowcount
        elif older_than_days is not None:
            n = c.execute("DELETE FROM predictions WHERE created_at < datetime('now', ?)", (f"-{int(older_than_days)} days",)).rowcount
        else:
            n = c.execute("DELETE FROM predictions").rowcount
    audit(actor, "predictions_deleted", f"{n} rows")
    return n


def clear_audit(actor):
    with _db() as c:
        n = c.execute("DELETE FROM audit").rowcount
    audit(actor, "audit_cleared", f"{n} rows")
    return n


# ---------------------------------------------------------------- system
def table_counts():
    with _db() as c:
        return {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("users", "predictions", "audit")}


def db_size():
    return os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0


def backup_bytes():
    with _db() as src, tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        dst = sqlite3.connect(tmp.name)
        src.backup(dst)
        dst.close()
        return open(tmp.name, "rb").read()


def restore(data: bytes, actor):
    if not data.startswith(b"SQLite format 3"):
        return False, "That file is not a SQLite database."
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
    try:
        chk = sqlite3.connect(path)
        tables = {r[0] for r in chk.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        chk.close()
        if not {"users", "predictions", "audit", "settings"} <= tables:
            return False, "This backup is missing required tables."
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DB_PATH, "wb") as f:
            f.write(data)
    finally:
        os.unlink(path)
    init_db(*_ADMIN_CREDS)
    audit(actor, "database_restored", f"{len(data)} bytes")
    return True, "Backup restored."
