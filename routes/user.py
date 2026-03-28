import os,sqlite3

from flask import Blueprint, url_for,render_template, request, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user

from extensions import login_manager
from utils.database import get_db_connection
from models.__init__ import User

from werkzeug.security import check_password_hash, generate_password_hash

user_bp = Blueprint("user",__name__)

"""
================
   用户管理模块
================
功能:
- load_user:用户加载
- login:用户登录
- register:用户注册
- profile:用户页面信息
- logout:用户登出
- edit_profile:用户编辑
================

维护:elysianx
更新:2026.3.28 

================
"""

# === 加载用户 ===
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    u = conn.execute("SELECT * FROM users WHERE id= ?",(user_id,)).fetchone()
    conn.close()
    if u:
        return User(
            u['id'],
            u['username'] or '',
            u['bio'] or '',
            u['role'] or 'visitor',
            u['email'] or ''
        )
    return None
# === 加载完毕 ===

# === 用户登录 ===
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            login_user(User(
                user['id'],
                user['username'] or '',
                user['bio'] or '',
                user['role'] or 'visitor',
                user['email'] or ''
            ))
            return redirect('/')

        flash('用户名或密码错误', 'danger')

    return render_template('login.html')
# =============

# === 用户注册 ===
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    ADMIN_CODE = os.getenv('ADMIN_CODE',"RANDOM_KEY")
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            if request.form.get('admin_code') == ADMIN_CODE:
                role = 'admin'
            else:
                role = 'visitor'
            conn.execute(
                "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                (request.form['username'],
                 generate_password_hash(request.form['password']),
                 request.form.get('email', ''),
                 role)
            )
            conn.commit()
            conn.close()
            flash('注册成功，请登录', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('用户名已存在', 'danger')
            conn.close()
    return render_template('register.html')
# ==========

# === 用户页面 ===
@user_bp.route('/profile/<username>', methods=['GET'])
@login_required
def profile(username):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page-1) * per_page

    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) as count FROM articles WHERE author = ? AND status >= 1 ORDER BY date DESC LIMIT  ? OFFSET  ?",(username,per_page,offset)).fetchone()['count']
    u = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    u_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND status >= 1", (username,)).fetchall()
    conn.close()
    total_pages = (total + per_page - 1) // per_page
    if u is None:
        return "用户不存在", 404
    return render_template('profile.html', user=u,user_articles=u_articles,page=page,per_page=per_page,total_pages=total_pages,total = total)
# =======

# === 用户登出 ===
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')
# ==============

# === 用户编辑 ===
@user_bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET username = ?, bio = ?, email = ? WHERE id = ?',
                    (request.form['username'], request.form['bio'], request.form['email'], current_user.id))
        conn.commit()
        current_user.username = request.form['username']
        flash('资料更新成功', 'success')
    except sqlite3.IntegrityError:
        flash('用户名已存在', 'danger')
    finally:
        conn.close()
    return redirect(url_for("profile", username=current_user.username))

# =================