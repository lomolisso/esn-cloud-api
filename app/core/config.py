import os
from dotenv import load_dotenv

# Retrieve enviroment variables from .env file
load_dotenv()

SECRET_KEY: str = os.environ.get("SECRET_KEY")

DATA_MICROSERVICE_URL: str = os.environ.get("DATA_MICROSERVICE_URL")
COMMAND_MICROSERVICE_URL: str = os.environ.get("COMMAND_MICROSERVICE_URL")
INFERENCE_MICROSERVICE_URL: str = os.environ.get("INFERENCE_MICROSERVICE_URL")

LATENCY_BENCHMARK: bool = bool(int(os.environ.get("LATENCY_BENCHMARK", "0")))
ADAPTIVE_INFERENCE: bool = bool(int(os.environ.get("ADAPTIVE_INFERENCE", "1")))
POLLING_INTERVAL_MS: int = int(os.environ.get("POLLING_INTERVAL_MS", "100"))

CLOUD_INFERENCE_LAYER: int = 2
GATEWAY_INFERENCE_LAYER: int = 1
SENSOR_INFERENCE_LAYER: int = 0
HEURISTIC_ERROR_CODE: int = -1

ORIGINS: list = [
    "*"
]