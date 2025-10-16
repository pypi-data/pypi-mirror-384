"""
Example user domain router demonstrating `require_roles`.
"""

from fastapi import APIRouter, Depends

from spaps_server_quickstart.auth import AuthenticatedUser
from spaps_server_quickstart.rbac import require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", summary="List users")
async def list_users(current_user: AuthenticatedUser = Depends(require_roles(["staff", "admin"]))) -> dict[str, str]:
    return {"message": "List users", "requested_by": current_user.user_id}


@router.get("/{user_id}", summary="Retrieve a user profile")
async def get_user(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_roles(["staff", "admin"])),
) -> dict[str, str]:
    return {"user_id": user_id, "requested_by": current_user.user_id}
