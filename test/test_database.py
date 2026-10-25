
from services.database import (
    DATABASE_PATH,
    initialize_database,
    save_parcel,
    update_parcel_status,
    get_parcel,
    get_all_parcels,
)


def main():
    initialize_database()
    print(f"Database initialized: {DATABASE_PATH}")

    parcel = {
        "parcel_id": "DBTEST001",
        "sender_name": "Test Sender",
        "recipient_name": "Test Recipient",
        "pickup_location": "Colombo",
        "delivery_location": "Kandy",
        "size": "medium",
        "weight_kg": 3.5,
        "priority": "high",
        "status": "REGISTERED",
    }

    save_parcel(parcel)
    print("Parcel saved successfully.")

    saved = get_parcel("DBTEST001")
    print("Saved parcel:", saved)

    update_parcel_status("DBTEST001", "ALLOCATED")

    updated = get_parcel("DBTEST001")
    print("Updated status:", updated["status"])

    print("Total stored parcels:", len(get_all_parcels()))


if __name__ == "__main__":
    main()
