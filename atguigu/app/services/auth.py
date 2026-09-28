import jwt
from fastapi import HTTPException, status
from pydantic import ValidationError

from atguigu.app.schemas.auth import CurrentUser
from atguigu.common.config import get_settings


class AuthService:
    """解析 Customer Service 转发的用户 JWT。"""

    def __init__(self):
        self.settings = get_settings()

    def get_authorized_user(
            self,
            authorization: str | None,
            required_role: str
    ) -> CurrentUser:
        """解析当前用户并校验接口要求的身份。"""
        token = self.get_bearer_token(authorization)
        current_user = self._decode_access_token(token)
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="当前用户没有接口访问权限"
            )
        return current_user

    @staticmethod
    def get_bearer_token(
            authorization: str | None
    ) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer Token 必须提供"
            )
        return authorization.split(" ", 1)[1]

    def _decode_access_token(self, token: str) -> CurrentUser:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm]
            )
            return CurrentUser.model_validate(payload)
        except (jwt.PyJWTError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效令牌或者令牌过期"
            ) from exc
