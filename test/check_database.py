
from services.database import (
    initialize_database,
    save_courier,
    get_courier,
    get_all_couriers,
)


def main():
    initialize_database()

    courier = {
        "courier_id": "C001",
        "jid": "courier1@localhost",
        "available": True,
        "capacity_kg": 10.0,
        "remaining_capacity_kg": 10.0,
        "delivery_locations": ["Colombo", "Kandy"],
    }

    # Insert the test courier if it does not already exist.
    existing = get_courier("C001")

    if existing is None:
        save_courier(courier)

    saved = get_courier("C001")

    print("Courier record:")
    print(saved)

    print("\nAll couriers:")
    for item in get_all_couriers():
        print(item)


if __name__ == "__main__":
    main()
