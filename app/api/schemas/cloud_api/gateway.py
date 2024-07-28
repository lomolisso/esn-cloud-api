from pydantic import BaseModel
from typing import Optional
import enum


class Metadata(BaseModel):
    gateway_name: str
    sensor_name: str

class BaseExport(BaseModel):
    metadata: Metadata
    export_value: object


# --- Export: Sensor Reading ---

class SensorReading(BaseModel):
    uuid: str
    values: list[list[float]]

class SensorReadingExport(BaseExport):
    export_value: SensorReading

# --- Export: Inference Latency Benchmark ---

class InferenceLatencyBenchmark(BaseModel):
    reading_uuid: str
    send_timestamp: int
    recv_timestamp: int
    inference_latency: int

class InferenceLatencyBenchmarkExport(BaseExport):
    export_value: InferenceLatencyBenchmark

# --- Export: PredictionRequest ---

class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0

class InferenceDescriptor(BaseModel):
    inference_layer: InferenceLayer
    send_timestamp: int

class PredictionRequest(BaseModel):
    reading: SensorReading
    low_battery: bool
    inference_descriptor: InferenceDescriptor

class PredictionRequestExport(BaseExport):
    export_value: PredictionRequest

# --- Export: PredictionResult ---

class PredictionResult(BaseModel):
    reading_uuid: str
    send_timestamp: int
    inference_layer: InferenceLayer
    prediction: int
    heuristic_result: Optional[int] = None

class PredictionResultExport(BaseExport):
    export_value: PredictionResult
