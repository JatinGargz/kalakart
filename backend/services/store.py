"""SQLite store — products + orders, auto-seeded so the marketplace works day one."""
from __future__ import annotations
import json
import os
import sqlite3
import time

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shilp.db")

SEED_PRODUCTS = [
    {"name": "Handpainted Blue Pottery Plate", "craft": "Pottery", "price": 1250,
     "location": "Jaipur, Rajasthan", "artisan": "Rukmini Art",
     "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=500&q=60&auto=format&fit=crop",
     "description": "Handpainted plate in Jaipur's Persian blue-pottery technique with floral motifs.",
     "tags": ["blue-pottery", "jaipur", "handmade"]},
    {"name": "Terracotta Vase", "craft": "Pottery", "price": 1300,
     "location": "Asharikandi, Assam", "artisan": "Meera Kumbhar",
     "image_url": "https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=500&q=60&auto=format&fit=crop",
     "description": "Hand-coiled terracotta vase, sun-baked and polished with river pebbles.",
     "tags": ["terracotta", "vase", "eco-friendly"]},
    {"name": "Banarasi Silk Dupatta", "craft": "Textiles", "price": 1800,
     "location": "Varanasi, UP", "artisan": "Salma Ansari",
     "image_url": "https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=500&q=60&auto=format&fit=crop",
     "description": "Pure-silk Banarasi dupatta with gold zari butis, 40 hours on the handloom.",
     "tags": ["banarasi", "silk", "handloom"]},
    {"name": "Brass Diya Set (6 pc)", "craft": "Metalwork", "price": 950,
     "location": "Moradabad, UP", "artisan": "Iqbal Ahmed",
     "image_url": "https://images.unsplash.com/photo-1602523961358-f9f03dd557db?w=500&q=60&auto=format&fit=crop",
     "description": "Hand-cast brass diyas with engraved marigold pattern, set of six.",
     "tags": ["brass", "diya", "diwali"]},
    {"name": "Madhubani Painting", "craft": "Paintings", "price": 2400,
     "location": "Madhubani, Bihar", "artisan": "Sunita Devi",
     "image_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=500&q=60&auto=format&fit=crop",
     "description": "Original Madhubani fish-and-peacock painting, natural pigments on handmade paper.",
     "tags": ["madhubani", "painting", "bihar"]},
    {"name": "Wooden Carved Box", "craft": "Woodwork", "price": 1600,
     "location": "Saharanpur, UP", "artisan": "Naseem Suri",
     "image_url": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=500&q=60&auto=format&fit=crop",
     "description": "Sheesham keepsake box with deep-relief Mughal jaali carving.",
     "tags": ["wood", "carving", "gift"]},
    {"name": "Kutch Embroidered Cushion", "craft": "Textiles", "price": 750,
     "location": "Kutch, Gujarat", "artisan": "Jiviba Rabari",
     "image_url": "https://images.unsplash.com/photo-1584100936595-c065efbdec1e?w=500&q=60&auto=format&fit=crop",
     "description": "Mirror-work cushion cover in Rabari embroidery, 16-inch.",
     "tags": ["embroidery", "kutch", "home"]},
    {"name": "Bastar Dokra Elephant", "craft": "Metalwork", "price": 1450,
     "location": "Bastar, Chhattisgarh", "artisan": "Sukhram Sagar",
     "image_url": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=500&q=60&auto=format&fit=crop",
     "description": "Lost-wax Dokra brass elephant, 4000-year-old tribal craft.",
     "tags": ["dokra", "bastar", "brass"]},
    {"name": "Pashmina Shawl", "craft": "Textiles", "price": 3200,
     "location": "Kullu, HP", "artisan": "Tsering Bodh",
     "image_url": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=500&q=60&auto=format&fit=crop&crop=entropy",
     "description": "Hand-loomed pashmina shawl with Kullu border, feather-soft and warm.",
     "tags": ["pashmina", "shawl", "winter"]},
    {"name": "Warli Art Frame", "craft": "Paintings", "price": 1100,
     "location": "Palghar, Maharashtra", "artisan": "Jivya Mashe",
     "image_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=500&q=60&auto=format&fit=crop&crop=entropy",
     "description": "Warli tribal dance scene in geru red and rice white, framed.",
     "tags": ["warli", "tribal", "wall-art"]},
    {"name": "Rosewood Jewellery Box", "craft": "Woodwork", "price": 2100,
     "location": "Mysuru, Karnataka", "artisan": "Rahim Khan",
     "image_url": "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=500&q=60&auto=format&fit=crop",
     "description": "Rosewood box with sandalwood inlay, velvet-lined trays.",
     "tags": ["rosewood", "jewellery-box", "gift"]},
    {"name": "Terracotta Jewellery Set", "craft": "Jewellery", "price": 850,
     "location": "Kutch, Gujarat", "artisan": "Lakhi Ahir",
     "image_url": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=500&q=60&auto=format&fit=crop&crop=top",
     "description": "Baked-clay necklace and earrings, hand-painted in desert hues.",
     "tags": ["terracotta", "jewellery", "hand-painted"]},
]

SEED_ORDERS = [
    {"product": "Handpainted Blue Pottery Plate", "buyer": "Aman", "amount": 1200, "status": "Shipped"},
    {"product": "Terracotta Vase", "buyer": "Diya", "amount": 2300, "status": "Processing"},
    {"product": "Wooden Carved Box", "buyer": "Rohan", "amount": 1600, "status": "Confirmed"},
    {"product": "Banarasi Silk Dupatta", "buyer": "Kavya", "amount": 1800, "status": "Shipped"},
    {"product": "Brass Diya Set (6 pc)", "buyer": "Arjun", "amount": 950, "status": "Confirmed"},
]


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> dict:
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, craft TEXT,
        price REAL DEFAULT 0, location TEXT, artisan TEXT, image_url TEXT,
        description TEXT, tags TEXT DEFAULT '[]', created_at REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT, buyer TEXT,
        amount REAL DEFAULT 0, status TEXT DEFAULT 'Confirmed')""")
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, phone TEXT DEFAULT '',
        role TEXT DEFAULT 'artisan', pw_salt TEXT NOT NULL,
        pw_hash TEXT NOT NULL, created_at REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tokens(
        token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
        expires_at REAL NOT NULL)""")
    # seed products: insert any missing by name (safe for existing DBs)
    now = time.time()
    have = {r["name"] for r in c.execute("SELECT name FROM products").fetchall()}
    c.executemany(
        "INSERT INTO products(name,craft,price,location,artisan,image_url,description,tags,created_at)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        [(p["name"], p["craft"], p["price"], p["location"], p["artisan"],
          p["image_url"], p["description"], json.dumps(p["tags"]), now)
         for p in SEED_PRODUCTS if p["name"] not in have])
    no = c.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    if no == 0:
        c.executemany("INSERT INTO orders(product,buyer,amount,status) VALUES(?,?,?,?)",
                      [(o["product"], o["buyer"], o["amount"], o["status"]) for o in SEED_ORDERS])
    c.commit()
    np = c.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    no = c.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    c.close()
    return {"products": np, "orders": no, "db": DB}


def _row_to_product(r: sqlite3.Row) -> dict:
    try:
        tags = json.loads(r["tags"] or "[]")
    except Exception:
        tags = []
    return {"id": r["id"], "name": r["name"], "craft": r["craft"] or "",
            "price": r["price"] or 0, "location": r["location"] or "",
            "artisan": r["artisan"] or "", "image_url": r["image_url"] or "",
            "description": r["description"] or "", "tags": tags}


def list_products() -> list[dict]:
    c = _conn()
    rows = c.execute("SELECT * FROM products ORDER BY id").fetchall()
    c.close()
    return [_row_to_product(r) for r in rows]


def create_product(d: dict) -> int:
    c = _conn()
    cur = c.execute(
        "INSERT INTO products(name,craft,price,location,artisan,image_url,description,tags,created_at)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        (d.get("name", "Untitled"), d.get("craft", ""), float(d.get("price") or 0),
         d.get("location", ""), d.get("artisan", ""), d.get("image_url", ""),
         d.get("description", ""), json.dumps(d.get("tags") or []), time.time()))
    c.commit()
    pid = cur.lastrowid
    c.close()
    return pid


def list_orders() -> list[dict]:
    c = _conn()
    rows = c.execute("SELECT * FROM orders ORDER BY id").fetchall()
    c.close()
    return [{"id": r["id"], "product": r["product"], "buyer": r["buyer"],
             "amount": r["amount"], "status": r["status"]} for r in rows]


# ---------- users & tokens (hashlib only, no extra deps) ----------
def create_user(name: str, email: str, password: str, phone: str = "",
                role: str = "artisan") -> dict:
    import hashlib
    import secrets as _secrets
    email = (email or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Please enter a valid email address.")
    if len(password or "") < 4:
        raise ValueError("Password must be at least 4 characters.")
    if not (name or "").strip():
        raise ValueError("Please enter your name.")
    salt = _secrets.token_hex(16)
    ph = hashlib.pbkdf2_hmac("sha256", password.encode(),
                             bytes.fromhex(salt), 200_000).hex()
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users(name,email,phone,role,pw_salt,pw_hash,created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (name.strip(), email, phone.strip(), role or "artisan",
             salt, ph, time.time()))
        c.commit()
        uid = cur.lastrowid
    except sqlite3.IntegrityError:
        c.close()
        raise ValueError("This email is already registered. Please log in.")
    c.close()
    return {"id": uid, "name": name.strip(), "email": email, "role": role or "artisan"}


def _public_user(r: sqlite3.Row) -> dict:
    return {"id": r["id"], "name": r["name"], "email": r["email"],
            "phone": r["phone"] or "", "role": r["role"] or "artisan"}


def verify_user(email: str, password: str) -> dict | None:
    import hashlib
    c = _conn()
    r = c.execute("SELECT * FROM users WHERE email=?",
                  ((email or "").strip().lower(),)).fetchone()
    c.close()
    if not r:
        return None
    ph = hashlib.pbkdf2_hmac("sha256", (password or "").encode(),
                             bytes.fromhex(r["pw_salt"]), 200_000).hex()
    if ph != r["pw_hash"]:
        return None
    return _public_user(r)


def issue_token(user_id: int, days: int = 30) -> str:
    import hashlib
    import secrets as _secrets
    token = _secrets.token_urlsafe(32)
    th = hashlib.sha256(token.encode()).hexdigest()
    c = _conn()
    c.execute("INSERT INTO tokens(token_hash,user_id,expires_at) VALUES(?,?,?)",
              (th, user_id, time.time() + days * 86400))
    c.commit()
    c.close()
    return token


def user_from_token(token: str) -> dict | None:
    import hashlib
    if not token:
        return None
    th = hashlib.sha256(token.encode()).hexdigest()
    c = _conn()
    r = c.execute("SELECT u.* FROM users u JOIN tokens t ON t.user_id=u.id"
                  " WHERE t.token_hash=? AND t.expires_at>?", (th, time.time())).fetchone()
    c.close()
    return _public_user(r) if r else None


def revoke_token(token: str) -> None:
    import hashlib
    if not token:
        return
    c = _conn()
    c.execute("DELETE FROM tokens WHERE token_hash=?",
              (hashlib.sha256(token.encode()).hexdigest(),))
    c.commit()
    c.close()
