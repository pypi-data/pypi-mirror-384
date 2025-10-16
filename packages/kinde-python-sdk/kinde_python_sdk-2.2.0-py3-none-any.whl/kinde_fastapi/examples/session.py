from fastapi import Request
import secrets
from typing import Optional, Any, Dict
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class InMemorySessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        session_cookie: str = "session",
        max_age: int = 14 * 24 * 60 * 60,  # 14 days in seconds
        same_site: str = "lax",
        https_only: bool = False
    ):
        super().__init__(app)
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.same_site = same_site
        self.https_only = https_only
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Non-blocking lock for async context

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get(self.session_cookie)
        
        if not session_id:
            session_id = secrets.token_urlsafe(32)
            session_data = {}
        else:
            session_data = await self._get_session(session_id) or {}

        # Add session to request scope
        request.scope["session"] = session_data

        # Process the request
        response = await call_next(request)

        # Update session in memory
        if "session" in request.scope:
            await self._set_session(session_id, request.scope["session"])
            
            # Set cookie
            response.set_cookie(
                key=self.session_cookie,
                value=session_id,
                max_age=self.max_age,
                httponly=True,
                samesite=self.same_site,
                secure=self.https_only
            )

        return response

    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def _set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        async with self._lock:
            self._sessions[session_id] = data

    async def delete_session(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def cleanup_expired_sessions(self) -> None:
        """Optional: Method to clean up expired sessions if needed"""
        async with self._lock:
            # Implementation would depend on how you want to track session expiration
            pass 