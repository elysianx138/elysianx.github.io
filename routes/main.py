from flask import Blueprint,render_template
from flask_login import current_user
from flask import jsonify
from util.database import get_db_connection

"""
===============
   网站首页管理
===============
功能:
- index:网站首页展示

===============

维护:elysianx
更新:2026.4.18

===============
"""


main_bp = Blueprint('main', __name__)

# === 首页管理 ===
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/index')
def api_index():
    conn = get_db_connection()
    articles_num = conn.execute("SELECT COUNT(*) as count FROM articles WHERE status >= 1").fetchone()['count']
    users_num = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    files_num = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    articles = conn.execute("SELECT * FROM articles WHERE status >= 1 ORDER BY date DESC LIMIT 5").fetchall()
    conn.close()

    announcement = [dict(row) for row in ann]
    articles_list = [dict(row) for row in articles]
    stats = {'articles': articles_num, 'users': users_num, 'files': files_num}

    return jsonify({
        'success': True,
        'title': '首页',
        'hero_title': '欢迎来到 MyBlog',
        'hero_subtitle': '分享你的想法，记录你的故事',
        'article_label': '文章',
        'articles': articles_list,
        'stats': stats,
        'footer_text': '© 2026 MyBlog',
        'current_user': current_user.username if current_user.is_authenticated else None,
        'announcements': announcement,
    })
# ===============

# === 设置管理 ===
# @main_bp.route("/settings", methods=['GET'])
# def settings():
#     return render_template('settings.html')
# ==============

# === RSS 订阅 ===
@main_bp.route('/feed.xml')
def rss_feed():
    from flask import Response, request as req
    from xml.sax.saxutils import escape
    conn = get_db_connection()
    articles = conn.execute(
        "SELECT id, title, body, author, date, tag FROM articles WHERE status >= 1 ORDER BY date DESC LIMIT 20"
    ).fetchall()
    conn.close()

    base = req.url_root.rstrip('/')
    items = []
    for a in articles:
        link = f"{base}/article/{a['id']}"
        desc = escape((a['body'] or '')[:200])
        items.append(
            f"<item><title>{escape(a['title'])}</title>"
            f"<link>{link}</link><guid>{link}</guid>"
            f"<author>{escape(a['author'])}</author>"
            f"<pubDate>{escape(a['date'])}</pubDate>"
            f"<description>{desc}</description></item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        f'<title>MyBlog</title><link>{base}</link>'
        '<description>记录思想,分享见解</description>'
        f'{"".join(items)}'
        '</channel></rss>'
    )
    return Response(xml, mimetype='application/rss+xml')
# ===============


# === Sitemap ===
@main_bp.route('/sitemap.xml')
def sitemap():
    from flask import Response, request as req
    conn = get_db_connection()
    articles = conn.execute(
        "SELECT id, date FROM articles WHERE status >= 1 ORDER BY date DESC"
    ).fetchall()
    conn.close()

    base = req.url_root.rstrip('/')
    urls = [f"<url><loc>{base}/</loc></url>",
            f"<url><loc>{base}/articles_list</loc></url>",
            f"<url><loc>{base}/archive</loc></url>",
            f"<url><loc>{base}/tags</loc></url>"]
    for a in articles:
        urls.append(f"<url><loc>{base}/article/{a['id']}</loc><lastmod>{a['date']}</lastmod></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f'{"".join(urls)}</urlset>')
    return Response(xml, mimetype='application/xml')
# ===============