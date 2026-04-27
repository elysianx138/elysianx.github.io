import datetime
import re
import json

from flask import Blueprint,request,flash,redirect,url_for,render_template,abort
from flask_login import login_required, current_user

from util.database import get_db_connection

"""
==================
   文章系统管理
==================
功能:
- add:用户添加文章内容
- article_list:查看所有开源的文章列表
- my_articles:查看个人所有文章
- publish_article(article_id):用户开源文章(选择完全公开或者仅供浏览)
- search_article:搜索文章内容
- edit_article(action,article_id):编辑文章内容
- article_detail(article_id):查看文章详细内容
- open_article(article_id):用户完全公开文章内容
==================

维护:elysianx
更新:2026.3.28

==================
"""


articles_bp = Blueprint('articles_bp', __name__)

# === 文章添加 ===
@articles_bp.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    conn = get_db_connection()
    if request.method == 'POST':
        cursor = conn.cursor()
        status = int(request.form.get('status', 0))
        tag = request.form.get('tag', '') or ''
        title = request.form.get('title', '') or ''
        body = request.form.get('body', '') or ''
        author = current_user.username if current_user.username else ''

        cursor.execute(
            "INSERT INTO articles (title, body, author, date, reference, status,tag) VALUES (?, ?, ?, ?, '', ?,?)",
            (title, body, author,
             datetime.datetime.now().strftime("%Y-%m-%d"), status,tag)
        )

        new_article_id = cursor.lastrowid
        ref_title = re.findall(r'\[\[(.+?)\]\]', body)
        ref_ids = []
        for title_ref in ref_title:
            # 公开的文章 或 作者自己的文章 都可以被引用
            ref = conn.execute(
                "SELECT id FROM articles WHERE title = ? AND ((status >= 1) OR (author = ?))",
                (title_ref, author)
            ).fetchone()
            if ref:
                ref_ids.append(ref['id'])
        if ref_ids:
            conn.execute("UPDATE articles SET reference = ? WHERE id = ?", (json.dumps(ref_ids), new_article_id))

        conn.execute("DELETE FROM local_cache WHERE user_id = ?", (current_user.id,))
        conn.commit()
        conn.close()
        flash('文章保存成功', 'success')
        return redirect(url_for('my_articles'))

    # 可引用的文章：公开的 + 作者自己的（无论公开与否）
    open_article_list = [dict(row) for row in conn.execute(
        "SELECT id, title FROM articles WHERE (status >= 1) OR (author = ?)",
        (current_user.username,)
    ).fetchall()]
    conn.close()
    return render_template('add.html', open_article=open_article_list)
# ==========

# === 文章列表 ===
@articles_bp.route("/articles_list", methods=['GET'])
def article_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()

    # 只显示 status >= 1 的文章（仅浏览或完全公开）
    total = conn.execute("SELECT COUNT(*) as count FROM articles WHERE status >= 1").fetchone()['count']

    art = conn.execute("SELECT * FROM articles WHERE status >= 1 ORDER BY date DESC LIMIT ? OFFSET ? ",
                       (per_page, offset)).fetchall()
    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('articles_list.html', articles=art, total_pages=total_pages, page=page, per_page=per_page,
                           total=total)
# ====================

# === 个人文章展示 ===
@articles_bp.route("/my_articles")
@login_required
def my_articles():
    conn = get_db_connection()

    drafts = conn.execute("SELECT * FROM local_cache WHERE user_id = ?", (current_user.id,)).fetchall()
    private_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND (status = 0 OR status IS NULL)",
                                    (current_user.username,)).fetchall()
    public_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND status = 1",
                                   (current_user.username,)).fetchall()
    open_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND status = 2",
                                 (current_user.username,)).fetchall()

    conn.close()
    return render_template("my_articles.html",
                           drafts=drafts,
                           private_articles=private_articles,
                           public_articles=public_articles,
                           open_articles=open_articles)
# ==================


# === 开源文章 ===
@articles_bp.route("/article/<int:article_id>/publish", methods=['POST'])
@login_required
def publish_article(article_id):
    """发布为仅浏览(status=1)"""
    conn = get_db_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if article is None:
        conn.close()
        return "文章不存在", 404
    if article['author'] != current_user.username:
        flash('无权限', 'danger')
        conn.close()
        return redirect(url_for('article_detail', article_id=article_id))

    conn.execute("UPDATE articles SET status = 1 WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    flash('已发布为仅浏览', 'success')
    return redirect(url_for('article_detail', article_id=article_id))
# ===========


# === 文章搜索 ===
@articles_bp.route("/search")
def search_article():
    title = request.args.get('title', '')
    if title:
        conn = get_db_connection()
        article = conn.execute("SELECT id FROM articles WHERE title = ?", (title,)).fetchone()
        conn.close()
        if article:
            return redirect(url_for('article_detail', article_id=article['id']))
    return redirect(url_for('article_list'))
# ==============


# === 编辑文章 ===
@articles_bp.route("/article/<int:article_id>/<action>", methods=['POST',"GET"])
@login_required
def edit_article(action,article_id):
    conn = get_db_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if article is None:
        conn.close()
        return "文章不存在", 404
    if request.method == 'POST':
        if action == 'delete':
            if article['author'] == current_user.username or current_user.role == 'admin':
                conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                conn.commit()
                conn.close()
                flash("删除成功", "success")
                return redirect(url_for('article_list'))
            flash("删除失败", "danger")
            return redirect(url_for('article_list'))

        if action == 'edit':
            if article['author'] == current_user.username:
                conn.execute("UPDATE articles SET title = ?, body = ?, date = ? WHERE id = ?",(request.form['title'], request.form['body'], datetime.datetime.now().strftime("%Y-%m-%d"), article_id))
                conn.commit()
                conn.close()
                flash("编辑成功", "success")
                return redirect(url_for('article_list'))
            flash("编辑失败", "danger")
            return redirect(url_for('article_detail', article_id=article_id))
    all_articles = [dict(row) for row in conn.execute("SELECT id, title FROM articles").fetchall()]
    return render_template('edit_article.html', article=article,all_articles=all_articles)
# ===============

# === 详细文章内容 ===
@articles_bp.route("/article/<int:article_id>", methods=['GET'])
def article_detail(article_id):
    conn = get_db_connection()
    det = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if det is None:
        conn.close()
        return "文章不存在", 404

    # 权限检查：私人文章只有作者能看
    if det['status'] == 0 or det['status'] is None:
        if not current_user.is_authenticated or current_user.username != det['author']:
            conn.close()
            abort(403)

    backlinks = conn.execute("SELECT id,title FROM articles WHERE reference LIKE ? ", (f'%{article_id}%',)).fetchall()

    reading = det['reading'] + 1
    tag = det['tag']
    conn.execute("UPDATE articles SET reading = ? WHERE id = ?", (reading, article_id))
    conn.commit()

    try:
        ref_count = len(json.loads(det['reference'])) if det['reference'] else 0
    except:
        ref_count = 0
    backlink_count = len(backlinks)

    # 获取批注列表
    annotations = conn.execute("SELECT * FROM annotations WHERE article_id = ? ORDER BY created_at DESC",
                               (article_id,)).fetchall()

    conn.close()
    return render_template('article_detail.html', detail=det, backlinks=backlinks, ref_count=ref_count,
                           backlink_count=backlink_count, annotations=annotations, reading=reading, tag=tag)
# =============

# === 完全公开文章 ===
@articles_bp.route("/article/<int:article_id>/open", methods=['POST'])
@login_required
def open_article(article_id):
    """开源(status=2)"""
    license = request.form.get('license', 'cc0')
    conn = get_db_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if article is None:
        conn.close()
        return "文章不存在", 404
    if article['author'] != current_user.username:
        flash('无权限', 'danger')
        conn.close()
        return redirect(url_for('article_detail', article_id=article_id))

    conn.execute("UPDATE articles SET status = 2, license = ? WHERE id = ?", (license, article_id))
    conn.commit()
    conn.close()
    flash('已开源', 'success')
    return redirect(url_for('article_detail', article_id=article_id))
# ============