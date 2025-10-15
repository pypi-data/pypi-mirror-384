from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class User:
    id: int
    name: str
    is_driver: bool = False


@dataclass
class Ride:
    id: int
    driver_id: int
    origin: str
    destination: str
    departure: datetime
    seats: int
    booked: List[int] = field(default_factory=list)  # list of rider_ids

    def seats_available(self) -> int:
        return self.seats - len(self.booked)


@dataclass
class Booking:
    id: int
    ride_id: int
    rider_id: int
    booked_at: datetime
    cancelled: bool = False
