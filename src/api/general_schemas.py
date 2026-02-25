from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str


class SuccessResponse(BaseModel):
    message: str