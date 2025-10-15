from datetime import datetime
from typing import List
from .models import User, Ride, Booking
from .storage import InMemoryStorage


class RideService:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage
        self.next_ride_id = 1
        self.next_booking_id = 1

    def register_user(self, user_id: int, name: str, is_driver: bool = False) -> User:
        user = User(id=user_id, name=name, is_driver=is_driver)
        self.storage.add_user(user)
        return user

    def create_ride(self, driver_id: int, origin: str, destination: str, departure: datetime, seats: int) -> Ride:
        if driver_id not in self.storage.users or not self.storage.users[driver_id].is_driver:
            raise ValueError("Driver not found or not registered as driver")

        ride = Ride(
            id=self.next_ride_id,
            driver_id=driver_id,
            origin=origin,
            destination=destination,
            departure=departure,
            seats=seats,
        )
        self.storage.add_ride(ride)
        self.next_ride_id += 1
        return ride

    def book_seat(self, ride_id: int, rider_id: int) -> Booking:
        if ride_id not in self.storage.rides:
            raise ValueError("Ride not found")
        if rider_id not in self.storage.users or self.storage.users[rider_id].is_driver:
            raise ValueError("Invalid rider")

        ride = self.storage.rides[ride_id]
        if ride.seats_available() <= 0:
            raise ValueError("No seats available")

        booking = Booking(
            id=self.next_booking_id,
            ride_id=ride_id,
            rider_id=rider_id,
            booked_at=datetime.now(),
        )
        self.storage.add_booking(booking)
        ride.booked.append(rider_id)
        self.next_booking_id += 1
        return booking

    def cancel_booking(self, booking_id: int):
        if booking_id not in self.storage.bookings:
            raise ValueError("Booking not found")

        booking = self.storage.bookings[booking_id]
        if booking.cancelled:
            raise ValueError("Booking already cancelled")

        booking.cancelled = True
        ride = self.storage.rides[booking.ride_id]
        ride.booked.remove(booking.rider_id)

    def find_rides(self, origin: str, destination: str) -> List[Ride]:
        return [
            ride for ride in self.storage.rides.values()
            if ride.origin == origin and ride.destination == destination and ride.seats_available() > 0
        ]
