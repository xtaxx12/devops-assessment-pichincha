from pydantic import BaseModel, ConfigDict, Field


class MessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1)
    to: str = Field(min_length=1)
    # "from" es palabra reservada en Python; se expone con alias para respetar el contrato JSON.
    sender: str = Field(min_length=1, alias="from")
    time_to_life_sec: int = Field(gt=0, alias="timeToLifeSec")


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    token: str
    transaction_id: str
    expires_in: int


class HealthResponse(BaseModel):
    status: str
    version: str
