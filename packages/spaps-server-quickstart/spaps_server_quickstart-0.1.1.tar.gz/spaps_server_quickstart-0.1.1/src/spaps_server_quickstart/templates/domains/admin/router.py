"""
Example admin domain router leveraging the RBAC helpers.
"""

from fastapi import APIRouter, Depends

from spaps_server_quickstart.auth import AuthenticatedUser
from spaps_server_quickstart.rbac import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", summary="Admin dashboard")
async def admin_dashboard(
    current_user: AuthenticatedUser = Depends(require_roles(["admin"], match="all")),
) -> dict[str, str]:
    return {"message": "Welcome to the admin dashboard", "requested_by": current_user.user_id}
