from pydantic import BaseModel
from typing import Optional
import enum


class Metadata(BaseModel):
    gateway_name: str
    sensor_name: str

class BaseExport(BaseModel):
    metadata: Metadata
    export_value: object

class CloudModel(BaseModel):
    tf_model_bytesize: int
    tf_model_b64: str

class SensorReading(BaseModel):
    uuid: str
    values: list[list[float]]

class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0

class InferenceDescriptor(BaseModel):
    inference_layer: InferenceLayer
    send_timestamp: int


# --- Prediction Request ---
class PredictionRequest(BaseModel):
    reading: SensorReading
    low_battery: bool
    inference_descriptor: InferenceDescriptor

class PredictionRequestExport(BaseExport):
    export_value: PredictionRequest


# --- Prediction Result ---

class PredictionResult(BaseModel):
    reading_uuid: str
    send_timestamp: int
    inference_layer: InferenceLayer
    prediction: int
    heuristic_result: Optional[int] = None

class PredictionResultExport(BaseExport):
    export_value: PredictionResult
