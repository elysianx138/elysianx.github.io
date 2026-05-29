from flask_login import LoginManager
# === 用户登录初始化 ===
login_manager = LoginManager()
login_manager.login_view = 'user.login'
# ===================