# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret_key"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "chatapp",
    "autocommit": True
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def get_friendship_between(conn, a, b):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM friendships
        WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
        LIMIT 1
    """, (a, b, b, a))
    row = cur.fetchone()
    cur.close()
    return row

def format_user_row(row):
    return {"id": row["id"], "prenom": row["prenom"], "nom": row["nom"]}

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, prenom, nom, email, password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["prenom"] = user["prenom"]
            session["nom"] = user["nom"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Email ou mot de passe incorrect")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not (prenom and nom and email and password and confirm):
            return render_template("register.html", error="Tous les champs sont requis")
        if password != confirm:
            return render_template("register.html", error="Les mots de passe ne correspondent pas")
        pw_hash = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (prenom, nom, email, password_hash) VALUES (%s, %s, %s, %s)",
                        (prenom, nom, email, pw_hash))
            conn.commit()
        except mysql.connector.IntegrityError:
            cur.close()
            conn.close()
            return render_template("register.html", error="Email déjà utilisé")
        cur.close()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", prenom=session.get("prenom"), nom=session.get("nom"))

@app.route("/api/users")
@login_required
def api_users():
    me = session["user_id"]
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, prenom, nom FROM users WHERE id != %s", (me,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([format_user_row(r) for r in rows])

@app.route("/api/friends")
@login_required
def api_friends():
    me = session["user_id"]
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT f.id as friendship_id, f.user_id, f.friend_id, f.status,
               u.id, u.prenom, u.nom
        FROM friendships f
        JOIN users u ON u.id = CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END
        WHERE (f.user_id = %s OR f.friend_id = %s) AND f.status IN ('accepted','blocked')
    """, (me, me, me))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "prenom": r["prenom"],
            "nom": r["nom"],
            "friendship_id": r["friendship_id"],
            "blocked": True if r["status"] == "blocked" else False,
            "status": r["status"]
        })
    return jsonify(out)

@app.route("/api/blocked")
@login_required
def api_blocked():
    me = session["user_id"]
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT f.id as friendship_id, u.id, u.prenom, u.nom
        FROM friendships f
        JOIN users u ON u.id = CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END
        WHERE (f.user_id = %s OR f.friend_id = %s) AND f.status = 'blocked'
    """, (me, me, me))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r["id"], "prenom": r["prenom"], "nom": r["nom"], "friendship_id": r["friendship_id"]} for r in rows])

@app.route("/api/requests")
@login_required
def api_requests():
    me = session["user_id"]
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT f.id as request_id, u.id as user_id, u.prenom, u.nom
        FROM friendships f
        JOIN users u ON u.id = f.user_id
        WHERE f.friend_id = %s AND f.status = 'pending'
        ORDER BY f.requested_at DESC
    """, (me,))
    received = cur.fetchall()
    cur.execute("""
        SELECT f.id as request_id, u.id as user_id, u.prenom, u.nom
        FROM friendships f
        JOIN users u ON u.id = f.friend_id
        WHERE f.user_id = %s AND f.status = 'pending'
        ORDER BY f.requested_at DESC
    """, (me,))
    sent = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({
        "received": [{"request_id": r["request_id"], "user_id": r["user_id"], "prenom": r["prenom"], "nom": r["nom"]} for r in received],
        "sent": [{"request_id": s["request_id"], "user_id": s["user_id"], "prenom": s["prenom"], "nom": s["nom"]} for s in sent]
    })

@app.route("/api/send_request", methods=["POST"])
@login_required
def api_send_request():
    me = session["user_id"]
    data = request.get_json() or {}
    target = data.get("target_id") or request.form.get("target_id")
    if not target:
        return jsonify({"error": "target_id requis"}), 400
    target = int(target)
    if target == me:
        return jsonify({"error": "cannot friend yourself"}), 400
    conn = get_db()
    existing = get_friendship_between(conn, me, target)
    cur = conn.cursor()
    if existing:
        cur.close()
        conn.close()
        return jsonify({"error": "Relation déjà existante"}), 400
    try:
        cur.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (%s, %s, 'pending')", (me, target))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/respond_request", methods=["POST"])
@login_required
def api_respond_request():
    me = session["user_id"]
    data = request.get_json() or {}
    request_id = data.get("request_id")
    action = data.get("action")
    if not request_id or action not in ("accept", "decline"):
        return jsonify({"error": "paramètres invalides"}), 400
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, user_id, friend_id FROM friendships WHERE id = %s", (request_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "request introuvable"}), 404
    # only friend_id can accept
    if row["friend_id"] != me:
        cur.close()
        conn.close()
        return jsonify({"error": "non autorisé"}), 403
    if action == "accept":
        cur2 = conn.cursor()
        cur2.execute("UPDATE friendships SET status = 'accepted' WHERE id = %s", (request_id,))
        conn.commit()
        cur2.close()
    else:
        cur2 = conn.cursor()
        cur2.execute("DELETE FROM friendships WHERE id = %s", (request_id,))
        conn.commit()
        cur2.close()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/block_friend", methods=["POST"])
@login_required
def api_block_friend():
    me = session["user_id"]
    data = request.get_json() or {}
    friendship_id = data.get("friendship_id") or data.get("friend_id")
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if friendship_id:
        cur.execute("SELECT * FROM friendships WHERE id = %s", (friendship_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": "friendship introuvable"}), 404
        if not (row["user_id"] == me or row["friend_id"] == me):
            cur.close()
            conn.close()
            return jsonify({"error": "non autorisé"}), 403
        upd = conn.cursor()
        upd.execute("UPDATE friendships SET status = 'blocked' WHERE id = %s", (friendship_id,))
        conn.commit()
        upd.close()
        cur.close()
        conn.close()
        return jsonify({"ok": True})
    else:
        friend_id = data.get("friend_id")
        if not friend_id:
            cur.close()
            conn.close()
            return jsonify({"error": "friend_id requis"}), 400
        friend_id = int(friend_id)
        existing = get_friendship_between(conn, me, friend_id)
        cur.close()
        if existing:
            upd = conn.cursor()
            upd.execute("UPDATE friendships SET status = 'blocked' WHERE id = %s", (existing["id"],))
            conn.commit()
            upd.close()
            conn.close()
            return jsonify({"ok": True})
        else:
            ins = conn.cursor()
            ins.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (%s, %s, 'blocked')", (me, friend_id))
            conn.commit()
            ins.close()
            conn.close()
            return jsonify({"ok": True})

@app.route("/api/unblock_friend", methods=["POST"])
@login_required
def api_unblock_friend():
    me = session["user_id"]
    data = request.get_json() or {}
    friendship_id = data.get("friendship_id") or data.get("friend_id")
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if friendship_id:
        cur.execute("SELECT * FROM friendships WHERE id = %s", (friendship_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": "introuvable"}), 404
        if not (row["user_id"] == me or row["friend_id"] == me):
            cur.close()
            conn.close()
            return jsonify({"error": "non autorisé"}), 403
        upd = conn.cursor()
        upd.execute("UPDATE friendships SET status = 'accepted' WHERE id = %s", (friendship_id,))
        conn.commit()
        upd.close()
        cur.close()
        conn.close()
        return jsonify({"ok": True})
    else:
        friend_id = data.get("friend_id")
        if not friend_id:
            cur.close()
            conn.close()
            return jsonify({"error": "friend_id requis"}), 400
        friend_id = int(friend_id)
        existing = get_friendship_between(conn, me, friend_id)
        if not existing:
            cur.close()
            conn.close()
            return jsonify({"error": "introuvable"}), 404
        upd = conn.cursor()
        upd.execute("UPDATE friendships SET status = 'accepted' WHERE id = %s", (existing["id"],))
        conn.commit()
        upd.close()
        cur.close()
        conn.close()
        return jsonify({"ok": True})

@app.route("/api/remove_friend", methods=["POST", "DELETE"])
@login_required
def api_remove_friend():
    me = session["user_id"]
    data = request.get_json() or {}
    friendship_id = data.get("friendship_id")
    friend_id = data.get("friend_id")
    conn = get_db()
    cur = conn.cursor()
    if friendship_id:
        cur.execute("DELETE FROM friendships WHERE id = %s AND (user_id = %s OR friend_id = %s)", (friendship_id, me, me))
    elif friend_id:
        cur.execute("DELETE FROM friendships WHERE ((user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s))", (me, friend_id, friend_id, me))
    else:
        cur.close()
        conn.close()
        return jsonify({"error": "friendship_id ou friend_id requis"}), 400
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/send_message", methods=["POST"])
@login_required
def api_send_message():
    me = session["user_id"]
    data = request.get_json() or {}
    to_id = data.get("to_id") or data.get("receiver_id")
    message = data.get("message", "").strip()
    if not to_id or not message:
        return jsonify({"error": "params manquants"}), 400
    to_id = int(to_id)
    conn = get_db()
    f = get_friendship_between(conn, me, to_id)
    if not f or f["status"] != "accepted":
        conn.close()
        return jsonify({"error": "vous n'êtes pas amis"}), 403
    if f["status"] == "blocked":
        conn.close()
        return jsonify({"error": "relation bloquée"}), 403
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)", (me, to_id, message))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/get_messages")
@login_required
def api_get_messages():
    me = session["user_id"]
    other = request.args.get("other", type=int)
    if not other:
        return jsonify({"error": "other param requis"}), 400
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, sender_id, receiver_id, message, sent_at
        FROM messages
        WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
        ORDER BY sent_at ASC
    """, (me, other, other, me))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route("/messages/<int:other>", methods=["GET"])
@login_required
def messages_alias(other):
    return api_get_messages()

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    app.run(debug=True)
