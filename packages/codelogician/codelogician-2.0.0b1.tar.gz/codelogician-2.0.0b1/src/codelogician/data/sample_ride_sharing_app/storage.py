from typing import Dict
from .models import User, Ride, Booking


class InMemoryStorage:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.rides: Dict[int, Ride] = {}
        self.bookings: Dict[int, Booking] = {}

    def add_user(self, user: User):
        self.users[user.id] = user

    def add_ride(self, ride: Ride):
        self.rides[ride.id] = ride

    def add_booking(self, booking: Booking):
        self.bookings[booking.id] = booking
