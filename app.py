import os,re,json
import sqlite3
import datetime
import secrets

from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask import render_template, request, redirect, flash, url_for, send_from_directory, abort, session, jsonify
import flask
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = flask.Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','RANDOM_KEY')

# === CSRF 保护 ===
@app.before_request
def csrf_protect():
    if request.method == "POST":
        # 忽略API路由的CSRF检查
        if request.path.startswith('/api/'):
            return
        token = session.get('csrf_token')
        if not token or token != request.form.get('csrf_token'):
            abort(403)

@app.context_processor
def csrf_token():
    def generate():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
        return session['csrf_token']
    return dict(csrf_token=generate)
# === CSRF 保护结束 ===

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'md', 'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists('uploads'):
    os.makedirs('uploads')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/uploads', methods=['POST','GET'])
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

@app.route('/files_list')
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


def get_db_connection():
    conn = sqlite3.connect("questions.db")
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id , username ,bio,role ,email):
        self.id,self.username,self.bio,self.role,self.email= id,username,bio,role,email

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

@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/register', methods=['GET', 'POST'])
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

@app.route('/profile/<username>', methods=['GET'])
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/edit_profile', methods=['POST'])
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

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    conn = get_db_connection()
    if request.method == 'POST':
        cursor = conn.cursor()
        status = int(request.form.get('status', 0))
        title = request.form.get('title', '') or ''
        body = request.form.get('body', '') or ''
        author = current_user.username if current_user.username else ''

        cursor.execute(
            "INSERT INTO articles (title, body, author, date, reference, status) VALUES (?, ?, ?, ?, '', ?)",
            (title, body, author,
             datetime.datetime.now().strftime("%Y-%m-%d"), status)
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

@app.route("/api/cache/save", methods=['POST'])
@login_required
def save_cache():
    data = request.get_json()
    title = data.get('title', '') or ''
    body = data.get('body', '') or ''
    
    conn = get_db_connection()
    cache = conn.execute("SELECT id FROM local_cache WHERE user_id = ?", (current_user.id,)).fetchone()

    if cache:
        conn.execute("UPDATE local_cache SET title = ?, body = ?, last_saved = ? WHERE user_id = ?",(title, body, datetime.datetime.now(), current_user.id))
    else:
        conn.execute("INSERT INTO local_cache (user_id, title, body) VALUES (?, ?, ?)",(current_user.id, title, body))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route("/api/cache/load", methods=['GET'])
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

@app.route("/api/cache/delete", methods=['POST'])
@login_required
def delete_cache():
    conn = get_db_connection()
    conn.execute("DELETE FROM local_cache WHERE user_id = ?", (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success':True})



@app.route("/settings", methods=['GET'])
def settings():
    return render_template('settings.html')

@app.route("/articles_list", methods=['GET'])
def article_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    
    # 只显示 status >= 1 的文章（仅浏览或完全公开）
    total = conn.execute("SELECT COUNT(*) as count FROM articles WHERE status >= 1").fetchone()['count']

    art = conn.execute("SELECT * FROM articles WHERE status >= 1 ORDER BY date DESC LIMIT ? OFFSET ? ",(per_page,offset)).fetchall()
    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('articles_list.html', articles=art, total_pages=total_pages, page=page, per_page=per_page , total = total)

@app.route("/search")
def search_article():
    title = request.args.get('title', '')
    if title:
        conn = get_db_connection()
        article = conn.execute("SELECT id FROM articles WHERE title = ?", (title,)).fetchone()
        conn.close()
        if article:
            return redirect(url_for('article_detail', article_id=article['id']))
    return redirect(url_for('article_list'))

@app.route("/my_articles")
@login_required
def my_articles():
    conn = get_db_connection()
    
    drafts = conn.execute("SELECT * FROM local_cache WHERE user_id = ?", (current_user.id,)).fetchall()
    private_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND (status = 0 OR status IS NULL)", (current_user.username,)).fetchall()
    public_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND status = 1", (current_user.username,)).fetchall()
    open_articles = conn.execute("SELECT * FROM articles WHERE author = ? AND status = 2", (current_user.username,)).fetchall()
    
    conn.close()
    return render_template("my_articles.html", 
                          drafts=drafts,
                          private_articles=private_articles,
                          public_articles=public_articles,
                          open_articles=open_articles)

@app.route("/article/<int:article_id>/publish", methods=['POST'])
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

@app.route("/article/<int:article_id>/open", methods=['POST'])
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

@app.route("/article/<int:article_id>", methods=['GET'])
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
    
    try:
        ref_count = len(json.loads(det['reference'])) if det['reference'] else 0
    except:
        ref_count = 0
    backlink_count = len(backlinks)
    
    # 获取批注列表
    annotations = conn.execute("SELECT * FROM annotations WHERE article_id = ? ORDER BY created_at DESC", (article_id,)).fetchall()

    conn.close()
    return render_template('article_detail.html', detail=det, backlinks=backlinks, ref_count=ref_count, backlink_count=backlink_count, annotations=annotations)

@app.route("/api/annotation/add", methods=['POST'])
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

@app.route("/article/<int:article_id>/<action>", methods=['POST',"GET"])
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


@app.route("/announcement/add", methods=['POST'])
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

@app.route("/announcement/delete", methods=['POST'])
@login_required
def announcement_delete():
    conn = get_db_connection()
    conn.execute("DELETE FROM announcement WHERE id = ?", (request.form['id'],))
    conn.commit()
    conn.close()
    flash('公告已删除', 'success')
    return redirect(url_for('admin'))

@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)
    conn = get_db_connection()
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    conn.close()
    return render_template('admin.html', announcements=ann)

@app.route('/')
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

if __name__ == '__main__':
    app.run(debug=True)
