from typing import Annotated, Optional, List

from fastapi import APIRouter, Header, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format
from square_database_structure.square.authentication.enums import RecoveryMethodEnum

from square_common_bl.configuration import (
    global_object_square_logger,
)
from square_common_bl.messages import messages
from square_common_bl.pydantic_models.authentication import (
    DeleteUserV0,
    LogoutAppsV0,
    ValidateEmailVerificationCodeV0,
    SendResetPasswordEmailV0,
)
from square_common_bl.utils.routes.authentication import (
    util_delete_user_v0,
    util_update_username_v0,
    util_get_user_details_v0,
    util_get_user_profile_photo_v0,
    util_update_profile_photo_v0,
    util_logout_all_v0,
    util_validate_email_verification_code_v0,
    util_send_verification_email_v0,
    util_update_profile_details_v0,
    util_send_reset_password_email_v0,
    util_generate_account_backup_codes_v0,
    util_update_user_recovery_methods_v0,
    util_logout_apps_v0,
)

router = APIRouter(
    tags=["authentication"],
)


@router.post("/delete_user/v0")
@global_object_square_logger.auto_logger()
async def delete_user_v0(
    access_token: Annotated[str, Header()],
    body: DeleteUserV0,
):
    try:
        return util_delete_user_v0(
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


@router.patch("/update_username/v0")
@global_object_square_logger.auto_logger()
async def update_username_v0(
    new_username: str,
    access_token: Annotated[str, Header()],
):
    try:
        return util_update_username_v0(
            new_username=new_username,
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


@router.get("/get_user_details/v0")
@global_object_square_logger.auto_logger()
async def get_user_details_v0(
    access_token: Annotated[str, Header()],
):
    try:
        return util_get_user_details_v0(
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


@router.get("/get_user_profile_photo/v0")
@global_object_square_logger.auto_logger()
async def get_user_profile_photo_v0(
    access_token: Annotated[str, Header()],
):
    try:
        return util_get_user_profile_photo_v0(
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


@router.patch("/update_profile_photo/v0")
@global_object_square_logger.auto_logger()
async def update_profile_photo_v0(
    access_token: Annotated[str, Header()],
    profile_photo: Optional[UploadFile] = None,
):
    try:
        return util_update_profile_photo_v0(
            access_token=access_token,
            profile_photo=profile_photo,
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


@router.delete("/logout/all/v0")
@global_object_square_logger.auto_logger()
async def logout_all_v0(
    access_token: Annotated[str, Header()],
):
    try:
        return util_logout_all_v0(
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


@router.delete("/logout/apps/v0")
@global_object_square_logger.auto_logger()
async def logout_apps_v0(
    access_token: Annotated[str, Header()],
    body: LogoutAppsV0,
):

    try:
        return util_logout_apps_v0(
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


@router.post("/validate_email_verification_code/v0")
@global_object_square_logger.auto_logger()
async def validate_email_verification_code_v0(
    access_token: Annotated[str, Header()],
    body: ValidateEmailVerificationCodeV0,
):
    try:
        return util_validate_email_verification_code_v0(
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


@router.post("/send_verification_email/v0")
@global_object_square_logger.auto_logger()
async def send_verification_email_v0(
    access_token: Annotated[str, Header()],
):
    try:
        return util_send_verification_email_v0(
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


@router.patch("/update_profile_details/v0")
@global_object_square_logger.auto_logger()
async def update_profile_details_v0(
    access_token: Annotated[str, Header()],
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number_country_code: Optional[str] = None,
    phone_number: Optional[str] = None,
):
    try:
        return util_update_profile_details_v0(
            access_token=access_token,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number_country_code=phone_number_country_code,
            phone_number=phone_number,
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


@router.post("/send_reset_password_email/v0")
@global_object_square_logger.auto_logger()
async def send_reset_password_email_v0(
    body: SendResetPasswordEmailV0,
):

    try:
        return util_send_reset_password_email_v0(
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


@router.post("/generate_account_backup_codes/v0")
@global_object_square_logger.auto_logger()
async def generate_account_backup_codes_v0(
    access_token: Annotated[str, Header()],
):
    try:
        return util_generate_account_backup_codes_v0(
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


@router.patch("/update_user_recovery_methods/v0")
@global_object_square_logger.auto_logger()
async def update_user_recovery_methods_v0(
    access_token: Annotated[str, Header()],
    recovery_methods_to_add: List[RecoveryMethodEnum] = None,
    recovery_methods_to_remove: List[RecoveryMethodEnum] = None,
):

    try:
        return util_update_user_recovery_methods_v0(
            access_token=access_token,
            recovery_methods_to_add=recovery_methods_to_add,
            recovery_methods_to_remove=recovery_methods_to_remove,
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
