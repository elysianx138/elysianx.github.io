import datetime

from flask import Blueprint, abort,render_template,request,flash,redirect,url_for
from flask_login import login_required, current_user

from utils.database import get_db_connection

"""
=================
   管理员管理系统
=================

功能:
- admin:显示管理员页面
- announcement_add:公告添加
- announcement_delete:公告删除

=================

维护:elysianx
更新:2026.3.28

=================
"""


admin_bp = Blueprint('admin_bp', __name__)

# === 管理员页面展示 ===
@admin_bp.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    conn.close()
    return render_template('admin.html', announcements=ann)
# ====================


# === 公告添加 ===
@admin_bp.route("/announcement/add", methods=['POST'])
@login_required
def announcement_add():
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO announcement (title, body, date) VALUES (?, ?, ?)",
        (request.form['title'], request.form['body'], datetime.datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()
    flash('公告发布成功', 'success')
    return redirect(url_for('admin'))
# ===============

# === 公告删除 ===
@admin_bp.route("/announcement/delete", methods=['POST'])
@login_required
def announcement_delete():
    conn = get_db_connection()
    conn.execute("DELETE FROM announcement WHERE id = ?", (request.form['id'],))
    conn.commit()
    conn.close()
    flash('公告已删除', 'success')
    return redirect(url_for('admin'))
# ===============