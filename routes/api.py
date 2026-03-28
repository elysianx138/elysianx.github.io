import datetime

from flask import Blueprint,request,jsonify
from flask_login import login_required, current_user

from utils.database import get_db_connection

"""
======================
   api数据传输模块
======================
功能:
- save_cache:每三十秒本地缓存自动保存草稿
- load_cache:加载保存草稿
- delete_cache:删除草稿
- add_annotation:添加注释,在完全公开的文章的内容中进行注释
======================

维护:elysianx
更新:2026.3.28

======================
"""


api_bp = Blueprint('api', __name__)

# === 保存草稿 ===
@api_bp.route("/api/cache/save", methods=['POST'])
@login_required
def save_cache():
    data = request.get_json()
    title = data.get('title', '') or ''
    body = data.get('body', '') or ''

    conn = get_db_connection()
    cache = conn.execute("SELECT id FROM local_cache WHERE user_id = ?", (current_user.id,)).fetchone()

    if cache:
        conn.execute("UPDATE local_cache SET title = ?, body = ?, last_saved = ? WHERE user_id = ?",
                     (title, body, datetime.datetime.now(), current_user.id))
    else:
        conn.execute("INSERT INTO local_cache (user_id, title, body) VALUES (?, ?, ?)", (current_user.id, title, body))

    conn.commit()
    conn.close()
    return jsonify({'success': True})
# ============


# === 加载草稿 ===
@api_bp.route("/api/cache/load", methods=['GET'])
@login_required
def load_cache():
    conn = get_db_connection()
    cache = conn.execute("SELECT id, title, body FROM local_cache WHERE user_id = ?", (current_user.id,)).fetchone()
    conn.close()

    if cache:
        return jsonify({
            'id': cache['id'] if cache['id'] else '',
            'title': cache['title'] if cache['title'] else '',
            'body': cache['body'] if cache['body'] else ''
        })
    return jsonify({'title': '', 'body': ''})
# ==============

# === 删除草稿 ===
@api_bp.route("/api/cache/delete", methods=['POST'])
@login_required
def delete_cache():
    conn = get_db_connection()
    conn.execute("DELETE FROM local_cache WHERE user_id = ?", (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})
# ==============

# === 添加注释 ===
@api_bp.route("/api/annotation/add", methods=['POST'])
@login_required
def add_annotation():
    data = request.get_json()
    article_id = data.get('article_id')
    target_text = data.get('target_text', '')
    content = data.get('content', '')
    color = data.get('color', '#ffeb3b')
    position_start = data.get('position_start', 0)
    position_end = data.get('position_end', 0)

    conn = get_db_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if article is None:
        conn.close()
        return jsonify({'error': '文章不存在'}), 404

    # 只有status=2(完全公开)的文章才能添加批注
    if article['status'] != 2:
        conn.close()
        return jsonify({'error': '只有完全公开的文章才能添加批注'}), 403

    conn.execute(
        "INSERT INTO annotations (article_id, author, target_text, content, position_start, position_end, color) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (article_id, current_user.username, target_text, content, position_start, position_end, color)
    )
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'id': new_id})
# ==============