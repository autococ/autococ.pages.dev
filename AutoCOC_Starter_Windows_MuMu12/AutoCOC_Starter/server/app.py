import os, sqlite3, secrets, string, hmac, hashlib, json, time
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, jsonify, render_template, abort
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
DB = os.getenv("DATABASE_PATH", "autococ.sqlite3")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:5000")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "change-this-immediately")
PLANS = {
    "7d": ("7 ngày", 29000, 7),
    "30d": ("30 ngày", 79000, 30),
    "90d": ("90 ngày", 189000, 90),
    "lifetime": ("Vĩnh viễn", 499000, None),
}
APP_VERSION = "0.1.0"
UPDATE_URL = os.getenv("UPDATE_URL", "")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS orders(
          id TEXT PRIMARY KEY, customer TEXT NOT NULL, email TEXT NOT NULL,
          plan TEXT NOT NULL, amount INTEGER NOT NULL, status TEXT NOT NULL,
          created_at TEXT NOT NULL, payment_ref TEXT
        );
        CREATE TABLE IF NOT EXISTS licenses(
          license_key TEXT PRIMARY KEY, order_id TEXT, plan TEXT NOT NULL,
          expires_at TEXT, status TEXT NOT NULL DEFAULT 'active',
          device_id TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, detail TEXT,
          created_at TEXT NOT NULL
        );
        """)

def audit(action, detail):
    with db() as c:
        c.execute("INSERT INTO audit(action,detail,created_at) VALUES(?,?,?)",
                  (action, detail[:500], datetime.now(timezone.utc).isoformat()))

def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*a, **kw)
    return wrapper

def make_key():
    alphabet = string.ascii_uppercase + string.digits
    chunks = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "ACOC-" + "-".join(chunks)

def issue_license(order):
    key = make_key()
    days = PLANS[order["plan"]][2]
    expires = None if days is None else (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    with db() as c:
        c.execute("INSERT INTO licenses(license_key,order_id,plan,expires_at,status,created_at) VALUES(?,?,?,?,?,?)",
                  (key, order["id"], order["plan"], expires, "active", datetime.now(timezone.utc).isoformat()))
        c.execute("UPDATE orders SET status='paid' WHERE id=?", (order["id"],))
    audit("license_issued", f"order={order['id']} key={key}")
    return key

@app.route("/")
def index():
    return render_template("index.html", plans=PLANS)

@app.route("/checkout", methods=["POST"])
def checkout():
    customer = request.form.get("customer", "").strip()
    email = request.form.get("email", "").strip()
    plan = request.form.get("plan", "")
    if not customer or "@" not in email or plan not in PLANS:
        flash("Vui lòng nhập tên, email hợp lệ và chọn gói key.")
        return redirect(url_for("index"))
    order_id = secrets.token_hex(8).upper()
    label, amount, _ = PLANS[plan]
    with db() as c:
        c.execute("INSERT INTO orders(id,customer,email,plan,amount,status,created_at) VALUES(?,?,?,?,?,?,?)",
                  (order_id, customer, email, plan, amount, "pending", datetime.now(timezone.utc).isoformat()))
    audit("order_created", f"{order_id} {email} {plan}")
    # MoMo is deliberately not marked paid here. Merchant credentials + verified IPN are required.
    return render_template("pending.html", order_id=order_id, customer=customer,
                           label=label, amount=amount, momo_ready=bool(os.getenv("MOMO_PARTNER_CODE")))

@app.route("/api/license/activate", methods=["POST"])
def activate():
    data = request.get_json(silent=True) or {}
    key = str(data.get("key", "")).strip().upper()
    device = str(data.get("device_id", "")).strip()[:128]
    if not key or not device:
        return jsonify(ok=False, message="Thiếu key hoặc mã thiết bị."), 400
    with db() as c:
        row = c.execute("SELECT * FROM licenses WHERE license_key=?", (key,)).fetchone()
        if not row or row["status"] != "active":
            return jsonify(ok=False, message="Key không hợp lệ hoặc đã bị khóa."), 403
        if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            return jsonify(ok=False, message="Key đã hết hạn."), 403
        if row["device_id"] and row["device_id"] != device:
            return jsonify(ok=False, message="Key đã được kích hoạt trên thiết bị khác."), 403
        c.execute("UPDATE licenses SET device_id=? WHERE license_key=?", (device, key))
    audit("license_activated", f"{key} device={device}")
    return jsonify(ok=True, plan=row["plan"], expires_at=row["expires_at"], version=APP_VERSION)

@app.route("/api/version")
def version():
    return jsonify(version=APP_VERSION, download_url=UPDATE_URL, notes="Bản khởi đầu Auto COC")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and hmac.compare_digest(request.form.get("password", ""), ADMIN_PASS):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Sai tài khoản hoặc mật khẩu.")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    with db() as c:
        orders = c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 100").fetchall()
        licenses = c.execute("SELECT * FROM licenses ORDER BY created_at DESC LIMIT 100").fetchall()
    return render_template("admin.html", orders=orders, licenses=licenses, plans=PLANS)

@app.route("/admin/confirm/<order_id>", methods=["POST"])
@admin_required
def confirm_order(order_id):
    with db() as c:
        order = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            abort(404)
        existing = c.execute("SELECT license_key FROM licenses WHERE order_id=?", (order_id,)).fetchone()
    if not existing:
        issue_license(order)
        flash("Đã xác nhận và cấp key. Chỉ xác nhận sau khi đã kiểm tra tiền vào tài khoản.")
    else:
        flash("Đơn này đã được cấp key.")
    return redirect(url_for("admin"))

@app.route("/admin/revoke/<key>", methods=["POST"])
@admin_required
def revoke(key):
    with db() as c:
        c.execute("UPDATE licenses SET status='revoked' WHERE license_key=?", (key,))
    audit("license_revoked", key)
    flash("Đã khóa key.")
    return redirect(url_for("admin"))

@app.route("/admin/create-key", methods=["POST"])
@admin_required
def create_manual_key():
    plan = request.form.get("plan")
    if plan not in PLANS:
        abort(400)
    order_id = "MANUAL-" + secrets.token_hex(4).upper()
    with db() as c:
        c.execute("INSERT INTO orders(id,customer,email,plan,amount,status,created_at) VALUES(?,?,?,?,?,?,?)",
                  (order_id, "Admin cấp tay", "-", plan, PLANS[plan][1], "paid",
                   datetime.now(timezone.utc).isoformat()))
        order = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    key = issue_license(order)
    flash(f"Key mới: {key}")
    return redirect(url_for("admin"))

@app.route("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION)

init_db()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
