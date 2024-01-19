from datetime import datetime
from pydantic import BaseModel
from typing import List


class BLEDeviceWithPoP(BaseModel):
    device_name: str
    device_address: str
    device_pop: str


class EdgeSensor(BaseModel):
    """
    Schema for returning an edge sensor.
    """

    device_name: str
    device_address: str
    uuid: str
    edgex_device_uuid: str
    registered_at: datetime

    class Config:
        from_attributes = True


class BaseEdgeGateway(BaseModel):
    """
    Basic register gateway request.
    """

    url: str


class EdgeGatewayIn(BaseEdgeGateway):
    """
    Schema for creating an edge gateway.
    """

    proof_of_possession: str


class EdgeGatewayOut(BaseEdgeGateway):
    uuid: str
    jwt_token: str

    device_name: str
    device_address: str
    registered_at: datetime

    edge_sensors: List[EdgeSensor] = []

    class Config:
        from_attributes = True


class MQTTConnectionStatus(BaseModel):
    device_name: str
    mqtt_connection_status: str


class EdgeSensorExportData(BaseModel):
    measurement: float

class EdgeSensorPredictionRequest(BaseModel):
    request_timestamp: str
    debug_mode: str
    measurement: float


class EdgeSensorPredictionLog(BaseModel):
    pred_source_layer: str
    request_timestamp: str
    response_timestamp: str
    measurement: float
    prediction: float


class EdgeSensorConfig(BaseModel):
    measurement_interval_ms: int
