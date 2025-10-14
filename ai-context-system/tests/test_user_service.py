"""
用户服务模块
提供用户管理功能
"""

class UserService:
    """用户服务类"""
    
    def __init__(self, database):
        """初始化用户服务"""
        self.database = database
        self.cache = {}
    
    def get_user(self, user_id: int) -> dict:
        """获取用户信息"""
        if user_id in self.cache:
            return self.cache[user_id]
        
        user = self.database.query(user_id)
        self.cache[user_id] = user
        return user
    
    def create_user(self, name: str, email: str) -> int:
        """创建新用户"""
        user_id = self.database.insert({
            "name": name,
            "email": email
        })
        return user_id
    
    def update_user(self, user_id: int, data: dict) -> bool:
        """更新用户信息"""
        success = self.database.update(user_id, data)
        if success and user_id in self.cache:
            del self.cache[user_id]
        return success


class UserRepository:
    """用户数据仓库"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def find_by_id(self, user_id: int):
        """根据ID查找用户"""
        return self.connection.execute(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        )
    
    def find_by_email(self, email: str):
        """根据邮箱查找用户"""
        return self.connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    """密码哈希"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
