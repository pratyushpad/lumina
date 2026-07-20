from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["config"])


@router.get("/api/config")
async def get_config():
    return {
        "model": settings.LLM_MODEL,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "top_k_reranked": settings.TOP_K_RERANKED,
        # The SPA runs the browser half of the OAuth flow, so it needs the
        # public client id and the exact redirect URI Google will accept. The
        # secret never leaves the server. When auth is off, the client id is
        # empty and the SPA hides sign-in entirely.
        "auth_enabled": settings.auth_enabled,
        "google_client_id": settings.GOOGLE_CLIENT_ID if settings.auth_enabled else "",
        "oauth_redirect_uri": settings.OAUTH_REDIRECT_URI if settings.auth_enabled else "",
    }
