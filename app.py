import os,flask,secrets
from dotenv import load_dotenv

from extensions import login_manager

from flask import request,abort, session

from routes import *

load_dotenv()

app = flask.Flask(__name__)

# === 密钥安全 ===
# 优先读取环境变量;未配置时生成一次性随机密钥(重启后 session 失效),
# 避免使用可被猜测的固定默认值导致 session 伪造。
_secret = os.getenv('SECRET_KEY')
if not _secret:
    _secret = secrets.token_hex(32)
    print("[WARN] 未设置 SECRET_KEY 环境变量,已生成临时随机密钥(重启后所有登录会话失效)。生产环境请在 .env 中配置 SECRET_KEY。")
app.secret_key = _secret
# ===============

login_manager.init_app(app)

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
    app.run(host="0.0.0.0",port=5000)
