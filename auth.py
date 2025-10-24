# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。

"""
认证模块
支持简单的 API Token 认证
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


class AuthManager:
    def __init__(self, auth_file: str = "./runtime/auth_tokens.json"):
        self.auth_file = Path(auth_file)
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        self.tokens = self._load_tokens()
        
    def _load_tokens(self):
        if self.auth_file.exists():
            try:
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_tokens(self):
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
        except Exception:
            pass
    
    def generate_token(self, name: str, expires_days: int = 365) -> str:
        """生成新的访问令牌"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        self.tokens[token_hash] = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
            "last_used": None
        }
        self._save_tokens()
        return token
    
    def verify_token(self, token: str) -> bool:
        """验证令牌是否有效"""
        if not token:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in self.tokens:
            return False
        
        token_data = self.tokens[token_hash]
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        
        if datetime.now() > expires_at:
            return False
        
        # 更新最后使用时间
        token_data["last_used"] = datetime.now().isoformat()
        self._save_tokens()
        
        return True
    
    def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.tokens:
            del self.tokens[token_hash]
            self._save_tokens()
            return True
        
        return False
    
    def list_tokens(self):
        """列出所有令牌"""
        result = []
        for token_hash, data in self.tokens.items():
            result.append({
                "hash": token_hash[:8] + "...",
                "name": data["name"],
                "created_at": data["created_at"],
                "expires_at": data["expires_at"],
                "last_used": data["last_used"]
            })
        return result


# 全局认证管理器
auth_manager = AuthManager()

# 是否启用认证
AUTH_ENABLED = False  # 默认关闭，可通过环境变量启用


async def verify_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> bool:
    """验证认证信息"""
    if not AUTH_ENABLED:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not auth_manager.verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True
