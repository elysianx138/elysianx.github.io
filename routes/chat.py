
from flask import Blueprint,redirect,render_template,request
from flask_login import current_user

from utils.about_chat_room import get_all_room, get_all_messages
from utils.database import get_db_connection

chat_bp = Blueprint('chat', __name__)

"""
==============
   聊天室管理
==============
功能:
- chat_room:聊天室页面加载显示
- chat_room(room_id):详细聊天室页面,展示聊天内容
- send_message(room_id):发送聊天室内容
==============

维护:elysianx
更新:2026.3.28

=============
"""


# === 聊天室加载 ===
@chat_bp.route('/chat')
def chat_rooms():
    return redirect('/chat/1')
# ================

# === 聊天室详细 ===
@chat_bp.route('/chat/<int:room_id>')
def chat_room(room_id):
    rooms = get_all_room()
    messages = get_all_messages(room_id)
    room_name = rooms[room_id-1]['name'] if room_id <= len(rooms) else '聊天室'
    return render_template('chat.html', room_name=room_name, messages=messages)
# ================

# === 聊天室信息发送 ===
@chat_bp.route('/chat/<int:room_id>/send', methods=['POST'])
def send_message(room_id):
    content = request.form.get('content').strip()
    conn = get_db_connection()
    conn.execute("INSERT INTO chat_messages (room_id,username,content) VALUES (?,?,?)",(room_id,current_user.username,content))
    conn.commit()
    conn.close()
    return redirect(f'/chat/{room_id}/')
# ===================