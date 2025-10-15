from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, Request, status
from pydantic import BaseModel


class DealerData(BaseModel):
    main_dealer_id: UUID | None = None


def get_dealer_data(
    request: Request,
    main_dealer_id: Annotated[
        UUID | None,
        Header(
            alias="main-dealer-id",
            description="Unique identifier of the primary dealer associated with the request."
        ),
    ] = None,
) -> DealerData:
    if main_dealer_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing main-dealer-id header",
        )

    return DealerData(
        main_dealer_id=main_dealer_id,
    )
