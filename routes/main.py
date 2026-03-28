from flask import Blueprint,render_template
from flask_login import current_user

from utils.database import get_db_connection

"""
===============
   网站首页管理
===============
功能:
- index:网站首页展示
- setting:网站设置展示
===============

维护:elysianx
更新:2026.3.28

===============
"""


main_bp = Blueprint('main', __name__)

# === 首页管理 ===
@main_bp.route('/')
def index():
    conn = get_db_connection()
    articles_num = conn.execute("SELECT COUNT(*) as count FROM articles WHERE status >= 1").fetchone()['count']
    users_num = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    files_num = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    articles = conn.execute("SELECT * FROM articles WHERE status >= 1 ORDER BY date DESC LIMIT 5").fetchall()
    conn.close()

    stats = {'articles': articles_num, 'users': users_num, 'files': files_num}

    return render_template('index.html',
                           title='首页',
                           hero_title='欢迎来到 MyBlog',
                           hero_subtitle='分享你的想法，记录你的故事',
                           article_label='文章',
                           articles=articles,
                           stats=stats,
                           footer_text='© 2026 MyBlog',
                           current_user=current_user,
                           announcements=ann
                           )
# ===============

# === 设置管理 ===
@main_bp.route("/settings", methods=['GET'])
def settings():
    return render_template('settings.html')
# ==============