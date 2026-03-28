import datetime
import os

from flask import Blueprint, send_from_directory, url_for, flash,request,redirect,render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from utils.database import get_db_connection
from utils.files import allowed_file

"""
===============
   文件相关管理
===============
功能:
- uploaded_file(filename):文件上传至指定文件夹uploads中
- uploads:文件上传
- files_list:文件详细列表展示
===============

维护:elysianx
更新:2026.3.28

===============
"""




files_bp = Blueprint('files', __name__)

# === 文件上传 ===
@files_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)
# ==============

# === 上传按钮 ===
@files_bp.route('/uploads', methods=['POST','GET'])
@login_required
def uploads():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有文件', 'danger')
            return redirect(url_for('files_list'))
        file = request.files['file']
        if file.filename == '':
            flash('没有文件', 'danger')
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('uploads', filename))
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO files (filepath, filename, uploader, date) VALUES (?, ?, ?, ?)",
                (f"uploads/{filename}", filename, current_user.username, datetime.datetime.now())
            )
            conn.commit()
            conn.close()
            flash('文件上传成功', 'success')
            return redirect(url_for('files_list'))
        flash('文件类型不支持', 'danger')
        return redirect(url_for('uploads'))
    return render_template('uploads.html')
# =============


# === 文件详细 ===
@files_bp.route('/files_list')
def files_list():
    conn = get_db_connection()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    f_list = conn.execute("SELECT * FROM files ORDER BY date DESC LIMIT ? OFFSET ?",(per_page,offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']

    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template("files_list.html", f_list=f_list,total_pages=total_pages,page=page,per_page=per_page,total = total)
# ===============