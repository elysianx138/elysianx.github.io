from .user import user_bp
from .chat import chat_bp
from .files import files_bp
from .articles import articles_bp
from .admin import admin_bp
from .api import api_bp
from .main import main_bp

"""
==================
   蓝图注册模块
==================
功能:
- 将所有模块的蓝图进行创建然后在app.py中进行注册

==================

维护:elysianx
更新:2026.3.28

==================
"""

__all__ = [
    'user_bp',
    'chat_bp',
    'files_bp',
    'articles_bp',
    'admin_bp',
    'api_bp',
    'main_bp'
]