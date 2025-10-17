from typing import Optional
from pydantic import BaseModel

from .inputs import InputModelInfo


class EstimatorCreationRequest(BaseModel):
    estimator_name: str
    session_id: str
    input_item_schema_b64: Optional[str] = None
    input_model_info: Optional[InputModelInfo] = None