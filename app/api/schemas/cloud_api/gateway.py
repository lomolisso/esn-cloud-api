import uuid
import enum
from pydantic import BaseModel
from typing import Optional

class Metadata(BaseModel):
    gateway_name: str
    sensor_name: str

class BaseExport(BaseModel):
    metadata: Metadata
    export_value: object

# --- Export: Inference Latency Benchmark ---
class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0

class InferenceLatencyBenchmark(BaseModel):
    sensor_name: str
    inference_layer: InferenceLayer
    send_timestamp: Optional[int] = None
    recv_timestamp: int
    inference_latency: int

class InferenceLatencyBenchmarkExport(BaseExport):
    export_value: InferenceLatencyBenchmark

# --- Export: SensorData ---
class SensorReading(BaseModel):
    uuid: str = str(uuid.uuid4())
    values: list[list[float]]


class InferenceDescriptor(BaseModel):
    inference_layer: InferenceLayer
    send_timestamp: Optional[int] = None
    recv_timestamp: Optional[int] = None
    prediction: Optional[int] = None

class SensorData(BaseModel):
    reading: SensorReading
    low_battery: bool
    inference_descriptor: InferenceDescriptor

class SensorDataExport(BaseExport):
    export_value: SensorData