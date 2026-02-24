import os
import sqlite3
from datetime import timedelta
from flask import Flask, render_template, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = "mohammed_almohsen_key_2026"
app.permanent_session_lifetime = timedelta(days=365) # الكوكيز تبقى لسنة

DATABASE = "database.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "0639296170"

# بيانات الأجزاء المعدة مسبقاً (يمكنك التوسع فيها)
SURAH_PARTS = {
    "البقرة": [
        {"id": 1, "text": "الجزء 1 (من 1 إلى 22)", "from": 1, "to": 22},
        {"id": 2, "text": "الجزء 2 (من 23 إلى 49)", "from": 23, "to": 49},
        {"id": 3, "text": "الجزء 3 (من 50 إلى 76)", "from": 50, "to": 76},
    ],
    "آل عمران": [
        {"id": 1, "text": "الجزء 1 (من 1 إلى 32)", "from": 1, "to": 32},
    ]
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db()
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, password TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS daily (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, surah TEXT, from_ayah INTEGER, to_ayah INTEGER, done INTEGER DEFAULT 0)")
        conn.commit()
        conn.close()

if not os.path.exists(DATABASE):
    init_db()

@app.route("/")
def home():
    if "user_id" in session: return redirect("/daily")
    if "admin" in session: return redirect("/admin")
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session.permanent = True
            session["admin"] = True
            return redirect("/admin")
        
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE phone=? AND password=?", (u, p)).fetchone()
        if user:
            session.permanent = True
            session["user_id"] = user['id']
            return redirect("/daily")
    return render_template("login.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if "admin" not in session: return redirect("/login")
    conn = get_db()
    
    if request.method == "POST":
        if "add_user" in request.form:
            conn.execute("INSERT INTO users (name, phone, password) VALUES (?,?,?)", 
                         (request.form["name"], request.form["phone"], request.form["password"]))
        elif "assign" in request.form:
            u_id = request.form["user_id"]
            surah = request.form["surah"]
            part_idx = int(request.form["part_index"])
            part_data = SURAH_PARTS[surah][part_idx]
            conn.execute("INSERT INTO daily (user_id, surah, from_ayah, to_ayah) VALUES (?,?,?,?)",
                         (u_id, surah, part_data["from"], part_data["to"]))
        elif "delete_user" in request.form:
            conn.execute("DELETE FROM users WHERE id=?", (request.form["u_id"],))
        conn.commit()

    users = conn.execute("SELECT * FROM users").fetchall()
    # جلب تقدم الجميع
    progress = conn.execute("SELECT users.name, daily.surah, daily.done FROM daily JOIN users ON daily.user_id = users.id").fetchall()
    conn.close()
    return render_template("admin.html", users=users, progress=progress, parts=SURAH_PARTS)

@app.route("/daily", methods=["GET","POST"])
def daily():
    if "user_id" not in session: return redirect("/login")
    conn = get_db()
    if request.method == "POST":
        conn.execute("UPDATE daily SET done=1 WHERE id=? AND user_id=?", (request.form["d_id"], session["user_id"]))
        conn.commit()
    
    my_tasks = conn.execute("SELECT * FROM daily WHERE user_id=?", (session["user_id"],)).fetchall()
    all_progress = conn.execute("SELECT users.name, daily.done FROM daily JOIN users ON daily.user_id = users.id").fetchall()
    conn.close()
    return render_template("daily.html", tasks=my_tasks, all_p=all_progress)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
app = app # تأكد أن هذا السطر موجود في نهاية الملف
