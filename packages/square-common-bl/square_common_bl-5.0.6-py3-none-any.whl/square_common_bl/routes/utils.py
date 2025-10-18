from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_common_bl.configuration import (
    global_object_square_logger,
)
from square_common_bl.messages import messages
from square_common_bl.utils.routes.utils import util_get_app_id_v0

router = APIRouter(
    tags=["utils"],
)


@router.get("/get_app_id/v0")
@global_object_square_logger.auto_logger()
async def get_app_id_v0(app_name: str):
    try:
        return util_get_app_id_v0(
            app_name=app_name,
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
