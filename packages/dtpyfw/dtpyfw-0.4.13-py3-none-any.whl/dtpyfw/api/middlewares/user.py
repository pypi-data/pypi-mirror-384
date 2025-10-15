import json
from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, ValidationError, Field


class UserRole(str, Enum):
    manager = "manager"
    administrator = "administrator"
    super_administrator = "super_administrator"


class PermissionType(str, Enum):
    dealer = "dealer"
    bulk_rule = "bulk_rule"
    inventory = "inventory"
    lead = "lead"
    page = "page"


class UserData(BaseModel):
    """Represents the authenticated user's identity, role, and access permissions."""

    id: UUID | None = Field(
        default=None,
        description="Unique identifier of the user."
    )
    role: UserRole | None = Field(
        default=None,
        description="Role assigned to the user, determining their level of access."
    )
    permissions: dict[UUID, list[PermissionType]] | None = Field(
        default=None,
        description="Mapping of dealer IDs to the list of permissions the user has for each dealer."
    )

    def check_accessibility(self, dealer_id: UUID | str) -> bool:
        """
        Check whether the user has access rights for the given dealer.

        Args:
            dealer_id (UUID | str): Dealer identifier (UUID or string).

        Returns:
            bool: True if the user has access, False otherwise.
        """
        # Administrators have universal access
        if self.role in {UserRole.super_administrator, UserRole.administrator}:
            return True

        # Normalize dealer_id to UUID
        uuid_dealer_id = dealer_id if isinstance(dealer_id, UUID) else UUID(str(dealer_id))

        # Check permissions mapping
        return bool(self.permissions and uuid_dealer_id in self.permissions)


def get_user_data(
    user_id: Annotated[
        UUID | None,
        Header(
            alias="user-id",
            description="Unique identifier of the user making the request."
        ),
    ] = None,
    user_role: Annotated[
        UserRole | None,
        Header(
            alias="user-role",
            description="Role assigned to the user making the request."
        ),
    ] = None,
    user_permissions: Annotated[
        str | None,
        Header(
            alias="user-permissions",
            description=(
                "JSON-encoded mapping of dealer IDs to the list of "
                "permissions granted to the user."
            ),
        ),
    ] = None,
) -> UserData:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user-id header"
        )

    perms = None
    if user_permissions:
        try:
            raw = json.loads(user_permissions)
            perms = {UUID(k): [PermissionType(p) for p in v] for k, v in raw.items()}
        except (json.JSONDecodeError, ValueError, TypeError, ValidationError):
            raise HTTPException(
                status_code=400, detail="Invalid user-permissions header JSON"
            )

    return UserData(id=user_id, role=user_role, permissions=perms)
