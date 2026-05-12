from util.database import get_db_connection

def get_all_room():
    conn = get_db_connection()
    rooms = conn.execute("SELECT * FROM chat_rooms").fetchall()
    conn.close()
    return rooms

def get_all_messages(room_id,limit = 100):
    conn = get_db_connection()
    messages = conn.execute("SELECT * FROM chat_messages WHERE room_id= ? ORDER BY created_at DESC LIMIT ?",(room_id,limit)).fetchall()
    conn.close()
    return messages