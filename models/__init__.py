from flask_login import UserMixin

# === 用户类 ===
class User(UserMixin):
    def __init__(self, id , username ,bio,role ,email):
        self.id,self.username,self.bio,self.role,self.email= id,username,bio,role,email
# =============
