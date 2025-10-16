import inspect
import functools
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from typing import Callable, Any, Optional

from acex.core.models import StoredDeviceConfig
from acex.constants import BASE_URL


def create_router(automation_engine):
    router = APIRouter(prefix=f"{BASE_URL}/operations")
    tags = ["Operations", "Device Configs"]

    dcm = automation_engine.device_config_manager
    router.add_api_route(
        "/device_configs/{hostname}",
        dcm.list_config_hashes,
        methods=["GET"],
        tags=["Device Config"]
    )
    router.add_api_route(
        "/device_configs/{hostname}/latest",
        dcm.get_latest_config,
        methods=["GET"],
        tags=["Device Config"]
    )
    router.add_api_route(
        "/device_configs/{hostname}/{hash}",
        dcm.get_config_by_hash,
        methods=["GET"],
        tags=["Device Config"]
    )
    router.add_api_route(
        "/device_configs/",
        dcm.upload_config,
        methods=["POST"],
        tags=["Device Config"]
    )
    return router




