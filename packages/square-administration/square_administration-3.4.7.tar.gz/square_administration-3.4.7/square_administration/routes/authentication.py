from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_administration.configuration import (
    global_object_square_logger,
)
from square_administration.messages import messages
from square_administration.pydantic_models.authentication import (
    RegisterUsernameV0,
    LoginUsernameV0,
    RemoveAppForSelfV0,
    RegisterLoginGoogleV0,
    ResetPasswordAndLoginUsingBackupCodeV0,
    ResetPasswordAndLoginUsingResetEmailCodeV0,
    UpdatePasswordV0,
)
from square_administration.utils.routes.authentication import (
    util_register_username_v0,
    util_login_username_v0,
    util_remove_app_for_self_v0,
    util_logout_v0,
    util_generate_access_token_v0,
    util_register_login_google_v0,
    util_reset_password_and_login_using_backup_code_v0,
    util_reset_password_and_login_using_reset_email_code_v0,
    util_update_password_v0,
)

router = APIRouter(
    tags=["authentication"],
)


@router.post("/register_username/v0")
@global_object_square_logger.auto_logger()
async def register_username_v0(
    body: RegisterUsernameV0,
):
    try:
        return util_register_username_v0(
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


@router.post("/login_username/v0")
@global_object_square_logger.auto_logger()
async def login_username_v0(
    body: LoginUsernameV0,
):
    try:
        return util_login_username_v0(
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


@router.patch("/remove_app_for_self/v0")
@global_object_square_logger.auto_logger()
async def remove_app_for_self_v0(
    access_token: Annotated[str, Header()],
    body: RemoveAppForSelfV0,
):
    try:
        return util_remove_app_for_self_v0(
            body=body,
            access_token=access_token,
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


@router.delete("/logout/v0")
@global_object_square_logger.auto_logger()
async def logout_v0(request: Request):
    try:
        return util_logout_v0(
            request=request,
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


@router.get("/generate_access_token/v0")
@global_object_square_logger.auto_logger()
async def generate_access_token_v0(
    request: Request,
):
    try:
        return util_generate_access_token_v0(
            request=request,
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


@router.post("/register_login_google/v0")
@global_object_square_logger.auto_logger()
async def register_login_google_v0(body: RegisterLoginGoogleV0):
    try:
        return util_register_login_google_v0(
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


@router.post("/reset_password_and_login_using_backup_code/v0")
@global_object_square_logger.auto_logger()
async def reset_password_and_login_using_backup_code_v0(
    body: ResetPasswordAndLoginUsingBackupCodeV0,
):
    try:
        return util_reset_password_and_login_using_backup_code_v0(
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


@router.post("/reset_password_and_login_using_reset_email_code/v0")
@global_object_square_logger.auto_logger()
async def reset_password_and_login_using_reset_email_code_v0(
    body: ResetPasswordAndLoginUsingResetEmailCodeV0,
):
    try:
        return util_reset_password_and_login_using_reset_email_code_v0(
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


@router.patch("/update_password/v0")
@global_object_square_logger.auto_logger()
async def update_password_v0(
    request: Request,
    body: UpdatePasswordV0,
    access_token: Annotated[str, Header()],
):
    try:
        return util_update_password_v0(
            request=request,
            body=body,
            access_token=access_token,
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
