
# === 文件的上传 ===

# 允许上传文件的白名单类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'md', 'txt', 'pdf', 'doc', 'docx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================