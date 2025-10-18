from typing import Annotated

from fastapi import APIRouter, Header, status, HTTPException
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_administration.configuration import (
    global_object_square_logger,
)
from square_administration.messages import messages
from square_administration.pydantic_models.core import GetAllGreetingsV0
from square_administration.utils.routes.core import util_get_all_greetings_v0

router = APIRouter(
    tags=["core"],
)


@router.post("/get_all_greetings/v0")
@global_object_square_logger.auto_logger()
async def get_all_greetings_v0(
    access_token: Annotated[str, Header()], body: GetAllGreetingsV0
):
    try:
        return util_get_all_greetings_v0(
            access_token=access_token,
            body=body,
        )
    except HTTPException as he:
        global_object_square_logger.logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        global_object_square_logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )
