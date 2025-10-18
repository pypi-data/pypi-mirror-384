from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_common_bl.configuration import (
    global_object_square_logger,
)
from square_common_bl.messages import messages
from square_common_bl.pydantic_models.greeting import (
    CreateAnonymousGreetingV0,
)
from square_common_bl.utils.routes.greeting import util_create_anonymous_greeting_v0

router = APIRouter(
    tags=["greeting"],
)


@router.post("/create_anonymous_greeting/v0")
@global_object_square_logger.auto_logger()
async def create_anonymous_greeting_v0(body: CreateAnonymousGreetingV0):
    try:
        return util_create_anonymous_greeting_v0(
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
