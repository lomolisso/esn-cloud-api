from datetime import datetime
from pydantic import BaseModel
from typing import List


class BaseEdgeSensor(BaseModel):
    """
    Basic edge sensor schema.
    """

    device_name: str
    device_address: str


class EdgeSensorIn(BaseEdgeSensor):
    """
    Schema for creating an edge sensor.
    """

    pass


class EdgeSensorOut(BaseEdgeSensor):
    """
    Schema for returning an edge sensor.
    """

    uuid: str
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

    edge_sensors: List[EdgeSensorOut] = []

    class Config:
        from_attributes = True


class MQTTConnectionStatus(BaseModel):
    device_name: str
    mqtt_connection_status: str


class _EdgeSensorMeasurement(BaseModel):
    resource_name: str
    value: str

class EdgeSensorMeasurements(BaseModel):
    device_name: str
    measurements: List[_EdgeSensorMeasurement]

class EdgeSensorConfig(BaseModel):
    ml_model: bool
    