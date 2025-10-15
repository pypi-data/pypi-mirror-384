from datetime import datetime, timedelta
from .storage import InMemoryStorage
from .services import RideService


def run_cli():
    storage = InMemoryStorage()
    service = RideService(storage)

    # Register users
    driver = service.register_user(1, "Alice", is_driver=True)
    rider1 = service.register_user(2, "Bob", is_driver=False)
    rider2 = service.register_user(3, "Charlie", is_driver=False)

    # Driver creates a ride
    ride = service.create_ride(driver.id, "Downtown", "Airport", datetime.now() + timedelta(hours=2), seats=2)

    # Riders search for rides
    print("== Available Rides ==")
    for r in service.find_rides("Downtown", "Airport"):
        print(f"Ride {r.id} by driver {r.driver_id}, seats available: {r.seats_available()}")

    # Riders book seats
    booking1 = service.book_seat(ride.id, rider1.id)
    booking2 = service.book_seat(ride.id, rider2.id)

    print("\n== After Bookings ==")
    for r in storage.rides.values():
        print(f"Ride {r.id} -> seats available: {r.seats_available()}")

    # Rider cancels booking
    service.cancel_booking(booking1.id)

    print("\n== After Cancellation ==")
    for r in storage.rides.values():
        print(f"Ride {r.id} -> seats available: {r.seats_available()}")

