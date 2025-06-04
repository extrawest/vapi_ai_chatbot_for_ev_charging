import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.models.schemas import RebootRequest, RebootResponse, StationStatus


class StationService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, '_initialized') or not self._initialized:
            self._stations: Dict[str, StationStatus] = {}
            self._initialize_mock_stations()
            self._initialized = True

    def _initialize_mock_stations(self) -> None:
        station_ids = ["ST001", "ST002", "ST003", "ST004", "ST005"]
        statuses = ["available", "occupied", "stuck", "error"]

        for station_id in station_ids:
            self._stations[station_id] = StationStatus(
                station_id=station_id,
                is_online=random.choice([True, True, True, False]),  # 75% online
                connector_status=random.choice(statuses),
                last_seen=datetime.now() - timedelta(minutes=random.randint(1, 60))
            )

    async def check_station_status(self, station_id: str) -> Optional[StationStatus]:
        await asyncio.sleep(random.uniform(0.5, 2.0))

        if station_id in self._stations:
            station = self._stations[station_id]

            if station_id == "ST001":
                station.is_online = True
                station.connector_status = "stuck"
                station.last_seen = datetime.now()
            elif random.random() < 0.1:
                statuses = ["available", "occupied", "stuck", "error"]
                station.connector_status = random.choice(statuses)
                station.last_seen = datetime.now()

            return station

        if station_id.startswith("ST") and len(station_id) == 5:
            new_station = StationStatus(
                station_id=station_id,
                is_online=random.choice([True, True, False]),
                connector_status=random.choice(["available", "occupied", "stuck", "error"]),
                last_seen=datetime.now() - timedelta(minutes=random.randint(1, 30))
            )
            self._stations[station_id] = new_station
            return new_station

        return None

    async def reboot_station(self, request: RebootRequest) -> RebootResponse:
        await asyncio.sleep(random.uniform(2.0, 5.0))

        station_id = request.station_id

        if station_id not in self._stations:
            return RebootResponse(
                success=False,
                message=f"Station {station_id} not found",
                station_id=station_id
            )

        station = self._stations[station_id]

        if not station.is_online:
            return RebootResponse(
                success=False,
                message=f"Station {station_id} is offline and cannot be rebooted",
                station_id=station_id
            )

        if random.random() < 0.9:
            station.connector_status = "available"
            station.last_seen = datetime.now()

            return RebootResponse(
                success=True,
                message=f"Station {station_id} rebooted successfully",
                station_id=station_id
            )
        else:
            return RebootResponse(
                success=False,
                message=f"Failed to reboot station {station_id}. Please contact technical support.",
                station_id=station_id
            )