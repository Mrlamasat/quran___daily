import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)
app.secret_key = "quran_daily_secret_key"

# --- إعدادات Supabase الخاصة بك ---
SUPABASE_URL = "https://wwiktewpowjuhjtpzpeu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind3aWt0ZXdwb3dqdWhqdHB6cGV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5MDIyMjEsImV4cCI6MjA4NzQ3ODIyMX0.TV2pmWxGZR4AvkjqYA1I_q0dZSSQPy-xxll1Mo1HxnU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- بيانات المسؤول (Admin) ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "0639296170"

# --- المسارات (Routes) ---

@app.route('/')
def index():
    if 'user' in session:
        if session['user'] == ADMIN_USERNAME:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # تسجيل دخول المسؤول
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['user'] = ADMIN_USERNAME
        return redirect(url_for('admin_dashboard'))

    # تسجيل دخول المستخدمين من قاعدة البيانات
    response = supabase.table('users').select("*").eq('username', username).eq('password', password).execute()
    
    if response.data:
        session['user'] = username
        return redirect(url_for('user_dashboard'))
    
    flash("خطأ في اسم المستخدم أو كلمة المرور")
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if session.get('user') != ADMIN_USERNAME:
        return redirect(url_for('index'))
    
    users = supabase.table('users').select("*").execute().data
    return render_template('admin.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    if session.get('user') != ADMIN_USERNAME:
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    phone = request.form.get('phone')

    supabase.table('users').insert({
        "name": name, 
        "username": username, 
        "password": password, 
        "phone": phone
    }).execute()
    
    flash("تم إضافة العضو بنجاح")
    return redirect(url_for('admin_dashboard'))

@app.route('/dashboard')
def user_dashboard():
    if 'user' not in session or session['user'] == ADMIN_USERNAME:
        return redirect(url_for('index'))
    
    username = session['user']
    user_data = supabase.table('users').select("*").eq('username', username).single().execute().data
    tasks = supabase.table('daily').select("*").eq('username', username).order('date', desc=True).execute().data
    
    return render_template('dashboard.html', user=user_data, tasks=tasks)

@app.route('/update_task', methods=['POST'])
def update_task():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    username = session['user']
    task_content = request.form.get('task')
    date_today = datetime.now().strftime('%Y-%m-%d')

    # تحديث أو إدخال ورد اليوم
    supabase.table('daily').upsert({
        "username": username,
        "date": date_today,
        "task": task_content
    }).execute()
    
    flash("تم تحديث الورد اليومي")
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
