
from services.database import (
    initialize_database,
    get_courier,
    save_courier,
)

def main():
    initialize_database()

    courier_id = "C001"
    courier = get_courier(courier_id)

    if courier is None:
        print(f"ERROR: Courier {courier_id} was not found.")
        return

    print("Courier state before reset:")
    print(courier)

    courier["remaining_capacity_kg"] = courier["capacity_kg"]
    courier["available"] = True

    save_courier(courier)

    updated_courier = get_courier(courier_id)

    print("\nCourier state after reset:")
    print(updated_courier)

    if (
        updated_courier
        and updated_courier["remaining_capacity_kg"]
        == updated_courier["capacity_kg"]
        and updated_courier["available"]
    ):
        print("\nSUCCESS: Courier restored for testing.")
    else:
        print("\nERROR: Courier state was not updated as expected.")

if __name__ == "__main__":
    main()
