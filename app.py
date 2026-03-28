import os,flask,secrets
from dotenv import load_dotenv

from extensions import login_manager

from flask import request,abort, session

from routes import *

app = flask.Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','RANDOM_KEY')

login_manager.init_app(app)

load_dotenv()

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



# === 创建保存内容的文件 ===
if not os.path.exists('uploads'):
    os.makedirs('uploads')
# ======================



# === 模块注册导入 ===
app.register_blueprint(user_bp)
app.register_blueprint(main_bp)
app.register_blueprint(files_bp)
app.register_blueprint(articles_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(api_bp)
# ==================


if __name__ == '__main__':
    app.run(debug=True)
