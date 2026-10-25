
from services.allocation import allocate_parcel


def make_courier(
    courier_id,
    locations,
    capacity,
    available=True,
):
    return {
        "courier_id": courier_id,
        "available": available,
        "delivery_locations": locations,
        "capacity_kg": capacity,
        "remaining_capacity_kg": capacity,
    }


def test_best_fit_allocation():
    print("\nTEST 1: Best-fit courier selection")

    parcel = {
        "parcel_id": "UNIT-P001",
        "delivery_location": "Kandy",
        "weight_kg": 3.5,
        "priority": "high",
    }

    couriers = [
        make_courier("C001", ["Colombo", "Kandy"], 5.5),
        make_courier("C002", ["Kandy"], 5.0),
        make_courier("C003", ["Kandy"], 20.0, available=False),
    ]

    selected = allocate_parcel(parcel, couriers)

    if selected is None:
        print("FAIL: No courier was selected.")
        return False

    print(f"Selected courier: {selected['courier_id']}")

    # Best fit should leave the least unused capacity.
    passed = selected["courier_id"] == "C002"

    print("PASS: Best-fit selection" if passed else "FAIL: Unexpected selection")
    return passed


def test_insufficient_capacity():
    print("\nTEST 2: Insufficient courier capacity")

    parcel = {
        "parcel_id": "UNIT-P002",
        "delivery_location": "Kandy",
        "weight_kg": 6.0,
        "priority": "high",
    }

    couriers = [
        make_courier("C001", ["Colombo", "Kandy"], 5.5),
        make_courier("C002", ["Kandy"], 5.0),
    ]

    selected = allocate_parcel(parcel, couriers)

    passed = selected is None

    print(
        "PASS: No courier selected because capacity is insufficient"
        if passed
        else "FAIL: A courier was selected unexpectedly"
    )

    return passed


def test_unavailable_courier():
    print("\nTEST 3: Unavailable courier")

    parcel = {
        "parcel_id": "UNIT-P003",
        "delivery_location": "Kandy",
        "weight_kg": 2.0,
        "priority": "normal",
    }

    couriers = [
        make_courier(
            "C003",
            ["Kandy"],
            20.0,
            available=False,
        ),
    ]

    selected = allocate_parcel(parcel, couriers)

    passed = selected is None

    print(
        "PASS: Unavailable courier was not selected"
        if passed
        else "FAIL: Unavailable courier was selected"
    )

    return passed


if __name__ == "__main__":
    results = [
        test_best_fit_allocation(),
        test_insufficient_capacity(),
        test_unavailable_courier(),
    ]

    print("\n========== TEST SUMMARY ==========")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("RESULT: ALL UNIT TESTS PASSED")
    else:
        print("RESULT: SOME TESTS FAILED")
