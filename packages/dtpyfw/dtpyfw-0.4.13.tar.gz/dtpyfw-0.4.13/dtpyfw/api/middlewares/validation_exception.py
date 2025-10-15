import json

from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse

from ..routes.response import return_response

__all__ = ("validation_exception_handler",)


async def validation_exception_handler(_, exc: ValidationException) -> JSONResponse:
    error = ""
    for error in exc.errors():
        location = " -> ".join([str(loc_item) for loc_item in error["loc"]])
        try:
            input_data = ", input: " + json.dumps(error["input"], default=str)
        except:
            input_data = ""

        error = (
            f"Error [location: '{location}'; message: '{error['msg']}'{input_data}'."
        )
        break

    return return_response(
        data=error,
        status_code=422,
        response_class=JSONResponse,
    )
