from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import enum

class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0

# --- Device Schemas ---
class BaseDeviceSchema(BaseModel):
    """
    Basic device schema.
    """
    device_name: str

# --- Edge Gateway Schemas ---

class CreateEdgeGateway(BaseDeviceSchema):
    """
    Schema for creating an edge gateway.
    """

    url: str
    device_address: str

class UpdateEdgeGateway(BaseDeviceSchema):
    """
    Schema for updating an edge gateway.
    """

    url: Optional[str] = None
    device_address:  Optional[str] = None

class ReadEdgeGateway(BaseDeviceSchema):
    """
    Schema for returning an edge gateway.
    """

    uuid: str
    device_address: str
    url: str
    registered_at: datetime


# --- Edge Sensor Schemas ---
class SensorState(str, enum.Enum):
    INITIAL = "initial"
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    WORKING = "working"
    IDLE = "idle"
    ERROR = "error"

class CreateEdgeSensor(BaseDeviceSchema):
    """
    Schema for creating an edge sensor.
    """
    device_address: str

class UpdateEdgeSensor(BaseDeviceSchema):
    """
    Schema for updating an edge sensor.
    """

    device_address:  Optional[str] = None
    state: Optional[SensorState] = None

class ReadEdgeSensor(BaseDeviceSchema):
    """
    Schema for returning an edge sensor.
    """

    uuid: str
    device_address: str
    registered_at: datetime

# --- Sensor Config Schemas ---
class SensorConfig(BaseModel):
    """
    Schema for a sensor configuration.
    """

    sleep_interval_ms: int


# --- Inference Latency Benchmark Schemas ---
class InferenceLatencyBenchmark(BaseModel):
    """
    Schema for an inference latency benchmark.
    """

    send_timestamp: int
    recv_timestamp: int
    inference_latency: int
    

# --- Inference Result Schemas ---
class PredictionResult(BaseModel):
    """
    Schema for an prediction result.
    """

    prediction: int
    inference_layer: InferenceLayer
    inference_latency_benchmark: Optional[InferenceLatencyBenchmark] = None


class BaseSensorReading(BaseModel):
    """
    Base schema for a sensor reading.
    """

    uuid: str
    values: str # JSON encoded list[list[float]]

class CreateSensorReading(BaseSensorReading):
    """
    Schema for creating a sensor reading.
    """

    pass

class ReadSensorReading(BaseSensorReading):
    """
    Schema for returning a sensor reading.
    """

    registered_at: datetime
    prediction_result: Optional[PredictionResult] = None
