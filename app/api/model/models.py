import uuid
import app.utils as utils

from app.database import Base
from sqlalchemy import Boolean, Float, ForeignKey, Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
    
class EdgeGateway(Base):
    __tablename__ = "edge_gateway_table"

    uuid = Column(UUID(as_uuid=False), primary_key=True, default=uuid.uuid4)
    jwt_token = Column(String(1000), unique=True)
    device_name = Column(String(50), unique=True)
    device_address = Column(String(17), unique=True)
    url = Column(Text, nullable=False, unique=True)
    proof_of_possession = Column(String(1000), nullable=False, unique=True)
    registered_at = Column(DateTime, default=utils.tz_now)    
    edge_sensors = relationship("EdgeSensor", backref="edge_gateway")


class EdgeSensor(Base):
    __tablename__ = "edge_sensor_table"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edgex_device_uuid = Column(UUID(as_uuid=True))
    working_state = Column(Boolean, nullable=False, default=False)
    device_name = Column(String(50), nullable=False, unique=True)
    device_address = Column(String(50), nullable=False, unique=True)
    registered_at = Column(DateTime, default=utils.tz_now)

    gateway_uuid = Column(UUID(as_uuid=True), ForeignKey("edge_gateway_table.uuid"))
    edge_sensor_prediction_logs = relationship("EdgeSensorPredictionLog", backref="edge_sensor")

class EdgeSensorPredictionLog(Base):
    __tablename__ = "edge_sensor_prediction_log_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String(50), nullable=False)
    pred_source_layer = Column(String(50), nullable=False)
    #request_timestamp = Column(String(50), nullable=False)
    #response_timestamp = Column(String(50), nullable=False)
    pred_latency = Column(Integer, nullable=False)
    measurement = Column(Float, nullable=False)
    prediction = Column(Float, nullable=False)

    edge_sensor_uuid = Column(UUID(as_uuid=True), ForeignKey("edge_sensor_table.uuid"))

