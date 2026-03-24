import os,re,json
import sqlite3
import datetime
import secrets
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask import render_template, request, redirect, flash, url_for, send_from_directory, abort, session
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
    return User(u['id'],u['username'],u['bio'],u['role'],u['email']) if u else None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['bio'], user['role'], user['email']))
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
    total = conn.execute("SELECT COUNT(*) as count FROM articles WHERE author = ? ORDER BY date DESC LIMIT  ? OFFSET  ?",(username,per_page,offset)).fetchone()['count']
    u = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    u_articles = conn.execute("SELECT * FROM articles WHERE author = ?", (username,)).fetchall()
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
        cursor.execute(
            "INSERT INTO articles (title, body, author, date, reference) VALUES (?, ?, ?, ?, '')",
            (request.form['title'], request.form['body'], current_user.username,
             datetime.datetime.now().strftime("%Y-%m-%d"))
        )

        new_article_id = cursor.lastrowid
        ref_title = re.findall(r'\[\[(.+?)\]\]', request.form['body'])
        ref_ids = []
        for title in ref_title:
            ref = conn.execute("SELECT id FROM articles WHERE title = ?", (title,)).fetchone()
            if ref:
                ref_ids.append(ref['id'])
        if ref_ids:
            conn.execute("UPDATE articles SET reference = ? WHERE id = ?", (json.dumps(ref_ids), new_article_id))
        conn.commit()
        conn.close()
        flash('文章发布成功', 'success')
        return redirect(url_for('add'))
    all_articles = [dict(row) for row in conn.execute("SELECT id, title FROM articles").fetchall()]
    conn.close()
    return render_template('add.html',all_articles=all_articles)

@app.route("/settings", methods=['GET'])
def settings():
    return render_template('settings.html')

@app.route("/articles_list", methods=['GET'])
def article_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) as count FROM articles").fetchone()['count']

    art = conn.execute("SELECT * FROM articles ORDER BY date DESC LIMIT ? OFFSET ? ",(per_page,offset)).fetchall()
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

@app.route("/article/<int:article_id>", methods=['GET'])
def article_detail(article_id):
    conn = get_db_connection()
    det = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    backlinks = conn.execute("SELECT id,title FROM articles WHERE reference LIKE ? ", (f'%{article_id}%',)).fetchall()
    
    try:
        ref_count = len(json.loads(det['reference'])) if det['reference'] else 0
    except:
        ref_count = 0
    backlink_count = len(backlinks)

    if det is None:
        conn.close()
        return "文章不存在", 404
    conn.close()
    return render_template('article_detail.html', detail=det, backlinks=backlinks, ref_count=ref_count, backlink_count=backlink_count)

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
    articles_num = conn.execute("SELECT COUNT(*) as count FROM articles").fetchone()['count']
    users_num = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    files_num = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    articles = conn.execute("SELECT * FROM articles ORDER BY date DESC LIMIT 5").fetchall()
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
