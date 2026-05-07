import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from supabase_auth.errors import AuthApiError

security = HTTPBearer()

user_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

admin_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


class AuthService:

    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        try:
            token = credentials.credentials

            user_response = user_supabase.auth.get_user(token)

            if not user_response.user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )

            return user_response.user

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

    def delete_user(self, user_id):
        admin_supabase.auth.admin.delete_user(user_id)


auth_service = AuthService()