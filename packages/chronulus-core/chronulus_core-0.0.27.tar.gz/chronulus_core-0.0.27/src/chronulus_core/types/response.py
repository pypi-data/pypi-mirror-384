from pydantic import BaseModel, Field
from typing import List, Optional

from chronulus_core.types.inputs import InputModelInfo
from chronulus_core.types.risk import Scorecard


class Response(BaseModel):
    success: bool
    message: str = Field(default="")


class QueuePredictionResponse(Response):
    request_id: str
    prediction_ids: List[str] = Field(default=list())


class UsageEstimateResponse(Response):
    chrons_estimate: Optional[float] = Field(default=None)


class SessionScorecardResponse(Response):
    session_id: str
    scorecard: Optional[Scorecard]


class Session(BaseModel):
    name: str
    situation: str
    task: str
    session_id: str


class SessionCreationResponse(Response):
    session_id: str
    flagged: bool = Field(default=False)


class SessionGetResponse(Response):
    session: Optional[Session] = Field(default=None)


class EstimatorCreationResponse(Response):
    estimator_id: Optional[str] = Field(default=None)


class EstimatorGetResponse(Response):
    estimator_id: str = Field(default=None)
    session: Optional[Session] = Field(default=None)
    input_model_info: Optional[InputModelInfo] = Field(default=None)


class PredictionGetByIdResponse(Response):
    response: Optional[dict] = Field(default=None)


class PredictionBatchGetByIdResponse(Response):
    responses: Optional[List[dict]] = Field(default=None)
    meta: Optional[dict] = Field(default=None)


class GetUploadUrlResponse(BaseModel):
    upload_id: str
    url: str

