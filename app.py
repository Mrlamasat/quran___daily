import os
from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "mohammed_almohsen_2026"

# --- استبدل هذه البيانات من حسابك في Supabase ---
SUPABASE_URL = "رابط_مشروعك_هنا"
SUPABASE_KEY = "مفتاح_API_الخاص_بك_هنا"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASSWORD = "0639296170"

# بيانات السور والأجزاء
SURAH_PARTS = {
    "البقرة": [
        {"id": 0, "text": "الجزء 1 (آية 1-141)", "from": 1, "to": 141},
        {"id": 1, "text": "الجزء 2 (آية 142-252)", "from": 142, "to": 252},
    ],
    "آل عمران": [
        {"id": 0, "text": "الجزء 3 (آية 1-200)", "from": 1, "to": 200},
    ]
}

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("daily"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        
        # دخول المسؤول
        if u == "admin" and p == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        
        # دخول الأعضاء من Supabase
        user_query = supabase.table("users").select("*").eq("phone", u).eq("password", p).execute()
        if user_query.data:
            session["user_id"] = user_query.data[0]['id']
            session["user_name"] = user_query.data[0]['name']
            return redirect(url_for("daily"))
            
    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        if "add_user" in request.form:
            supabase.table("users").insert({
                "name": request.form["name"],
                "phone": request.form["phone"],
                "password": request.form["password"]
            }).execute()
        elif "assign" in request.form:
            surah = request.form["surah"]
            p_idx = int(request.form["part_index"])
            part_data = SURAH_PARTS[surah][p_idx]
            supabase.table("daily").insert({
                "user_id": request.form["user_id"],
                "surah": surah,
                "from_ayah": part_data["from"],
                "to_ayah": part_data["to"],
                "done": 0
            }).execute()

    users = supabase.table("users").select("*").execute()
    progress = supabase.table("daily").select("*, users(name)").execute()
    return render_template("admin.html", users=users.data, progress=progress.data, parts=SURAH_PARTS)

@app.route("/daily", methods=["GET", "POST"])
def daily():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    uid = session["user_id"]
    if request.method == "POST":
        task_id = request.form.get("task_id")
        supabase.table("daily").update({"done": 1}).eq("id", task_id).execute()
    
    tasks = supabase.table("daily").select("*").eq("user_id", uid).execute()
    return render_template("daily.html", tasks=tasks.data, name=session.get("user_name"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# سطر مهم جداً لـ Vercel
app = app
