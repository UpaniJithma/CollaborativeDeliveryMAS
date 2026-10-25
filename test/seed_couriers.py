
"""
Seed 20 realistic simulated Sri Lankan courier agents.

Project:
    CollaborativeDeliveryMAS

Run from the project root:
    python seed_couriers.py

Safety:
- Uses the existing services.database module.
- Inserts only courier IDs that do not already exist.
- Does not delete or overwrite existing courier records.
- Does not modify parcel or allocation history.
- Creates simulated records, not real people or verified companies.

IMPORTANT:
The database module must provide:
    initialize_database()
    get_all_couriers()
    save_courier(courier_dict)
"""

from services.database import (
    initialize_database,
    get_all_couriers,
    save_courier,
)


# ---------------------------------------------------------
# 1. SIMULATED COURIER DATASET
# ---------------------------------------------------------

COURIERS = [
    {
        "courier_id": "C001",
        "jid": "courier1@localhost",
        "available": True,
        "capacity_kg": 10.0,
        "remaining_capacity_kg": 10.0,
        "delivery_locations": ["Colombo", "Kandy"],
    },
    {
        "courier_id": "C002",
        "jid": "courier2@localhost",
        "available": True,
        "capacity_kg": 15.0,
        "remaining_capacity_kg": 15.0,
        "delivery_locations": ["Colombo", "Gampaha", "Negombo"],
    },
    {
        "courier_id": "C003",
        "jid": "courier3@localhost",
        "available": True,
        "capacity_kg": 12.0,
        "remaining_capacity_kg": 12.0,
        "delivery_locations": ["Colombo", "Kalutara", "Panadura"],
    },
    {
        "courier_id": "C004",
        "jid": "courier4@localhost",
        "available": True,
        "capacity_kg": 20.0,
        "remaining_capacity_kg": 20.0,
        "delivery_locations": ["Kandy", "Matale", "Nuwara Eliya"],
    },
    {
        "courier_id": "C005",
        "jid": "courier5@localhost",
        "available": True,
        "capacity_kg": 18.0,
        "remaining_capacity_kg": 18.0,
        "delivery_locations": ["Galle", "Matara", "Hambantota"],
    },
    {
        "courier_id": "C006",
        "jid": "courier6@localhost",
        "available": True,
        "capacity_kg": 8.0,
        "remaining_capacity_kg": 8.0,
        "delivery_locations": ["Jaffna", "Kilinochchi", "Vavuniya"],
    },
    {
        "courier_id": "C007",
        "jid": "courier7@localhost",
        "available": True,
        "capacity_kg": 14.0,
        "remaining_capacity_kg": 14.0,
        "delivery_locations": ["Colombo", "Kandy", "Kurunegala"],
    },
    {
        "courier_id": "C008",
        "jid": "courier8@localhost",
        "available": False,
        "capacity_kg": 16.0,
        "remaining_capacity_kg": 16.0,
        "delivery_locations": ["Gampaha", "Negombo", "Puttalam"],
    },
    {
        "courier_id": "C009",
        "jid": "courier9@localhost",
        "available": True,
        "capacity_kg": 25.0,
        "remaining_capacity_kg": 25.0,
        "delivery_locations": ["Colombo", "Galle", "Matara"],
    },
    {
        "courier_id": "C010",
        "jid": "courier10@localhost",
        "available": True,
        "capacity_kg": 9.0,
        "remaining_capacity_kg": 9.0,
        "delivery_locations": [
            "Anuradhapura",
            "Vavuniya",
            "Trincomalee",
        ],
    },
    {
        "courier_id": "C011",
        "jid": "courier11@localhost",
        "available": True,
        "capacity_kg": 11.0,
        "remaining_capacity_kg": 11.0,
        "delivery_locations": ["Colombo", "Gampaha", "Kandy"],
    },
    {
        "courier_id": "C012",
        "jid": "courier12@localhost",
        "available": True,
        "capacity_kg": 30.0,
        "remaining_capacity_kg": 30.0,
        "delivery_locations": [
            "Colombo",
            "Kurunegala",
            "Anuradhapura",
        ],
    },
    {
        "courier_id": "C013",
        "jid": "courier13@localhost",
        "available": True,
        "capacity_kg": 7.5,
        "remaining_capacity_kg": 7.5,
        "delivery_locations": [
            "Batticaloa",
            "Ampara",
            "Trincomalee",
        ],
    },
    {
        "courier_id": "C014",
        "jid": "courier14@localhost",
        "available": True,
        "capacity_kg": 13.0,
        "remaining_capacity_kg": 13.0,
        "delivery_locations": [
            "Ratnapura",
            "Avissawella",
            "Colombo",
        ],
    },
    {
        "courier_id": "C015",
        "jid": "courier15@localhost",
        "available": True,
        "capacity_kg": 22.0,
        "remaining_capacity_kg": 22.0,
        "delivery_locations": [
            "Kandy",
            "Badulla",
            "Nuwara Eliya",
        ],
    },
    {
        "courier_id": "C016",
        "jid": "courier16@localhost",
        "available": False,
        "capacity_kg": 10.0,
        "remaining_capacity_kg": 10.0,
        "delivery_locations": ["Galle", "Matara", "Hambantota"],
    },
    {
        "courier_id": "C017",
        "jid": "courier17@localhost",
        "available": True,
        "capacity_kg": 17.0,
        "remaining_capacity_kg": 17.0,
        "delivery_locations": [
            "Jaffna",
            "Kilinochchi",
            "Mannar",
        ],
    },
    {
        "courier_id": "C018",
        "jid": "courier18@localhost",
        "available": True,
        "capacity_kg": 6.0,
        "remaining_capacity_kg": 6.0,
        "delivery_locations": [
            "Colombo",
            "Dehiwala",
            "Moratuwa",
        ],
    },
    {
        "courier_id": "C019",
        "jid": "courier19@localhost",
        "available": True,
        "capacity_kg": 19.0,
        "remaining_capacity_kg": 19.0,
        "delivery_locations": [
            "Kurunegala",
            "Puttalam",
            "Chilaw",
        ],
    },
    {
        "courier_id": "C020",
        "jid": "courier20@localhost",
        "available": True,
        "capacity_kg": 24.0,
        "remaining_capacity_kg": 24.0,
        "delivery_locations": [
            "Colombo",
            "Kandy",
            "Galle",
            "Jaffna",
        ],
    },
]


# ---------------------------------------------------------
# 2. SEED THE EXISTING SQLITE DATABASE
# ---------------------------------------------------------

def main():
    print("=" * 55)
    print("CollaborativeDeliveryMAS - Courier Dataset Seeder")
    print("=" * 55)

    # Initialize the existing database.
    initialize_database()

    # Read existing courier records.
    existing_couriers = get_all_couriers() or []

    # Identify IDs already stored in the database.
    existing_ids = {
        str(courier.get("courier_id", "")).strip().upper()
        for courier in existing_couriers
    }

    inserted_ids = []
    skipped_ids = []
    failed_ids = []

    # Insert missing couriers only.
    for courier in COURIERS:
        courier_id = courier["courier_id"]

        if courier_id in existing_ids:
            print(
                f"SKIPPED: {courier_id} already exists. "
                "Existing record preserved."
            )
            skipped_ids.append(courier_id)
            continue

        try:
            save_courier(courier)

            inserted_ids.append(courier_id)
            existing_ids.add(courier_id)

            print(
                f"INSERTED: {courier_id} | "
                f"Capacity: {courier['capacity_kg']} kg | "
                f"Available: {courier['available']} | "
                f"Areas: {', '.join(courier['delivery_locations'])}"
            )

        except Exception as error:
            failed_ids.append(courier_id)
            print(f"FAILED: {courier_id} | {error}")

    # Verify the resulting database state.
    final_couriers = get_all_couriers() or []

    target_ids = {
        courier["courier_id"] for courier in COURIERS
    }

    final_ids = {
        str(courier.get("courier_id", "")).strip().upper()
        for courier in final_couriers
    }

    missing_ids = sorted(target_ids - final_ids)

    # Print summary.
    print("\n" + "=" * 55)
    print("SEEDING SUMMARY")
    print("=" * 55)
    print(f"Target courier records: {len(COURIERS)}")
    print(f"New records inserted:   {len(inserted_ids)}")
    print(f"Existing records kept:  {len(skipped_ids)}")
    print(f"Insert failures:        {len(failed_ids)}")
    print(f"Total couriers in DB:   {len(final_couriers)}")

    if missing_ids:
        print("Target IDs still missing:", ", ".join(missing_ids))
    else:
        print("All target courier IDs C001-C020 are present.")

    if failed_ids:
        print("Failed IDs:", ", ".join(failed_ids))

    print("\nExisting parcel and allocation records were not targeted.")
    print(
        "Reminder: adding database records does not automatically "
        "start the corresponding SPADE agents."
    )


if __name__ == "__main__":
    main()
