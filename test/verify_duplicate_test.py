
from services.database import get_parcel, get_courier, get_all_allocations

parcel_id = "79bc14c5"
courier_id = "C001"

original_assignment_id = "5c9f263e-4711-4d10-bbde-181e7dd02c10"
duplicate_assignment_id = "ee840b33-a69d-45fd-9098-8b58189a1453"

print("\n========== FINAL VERIFICATION ==========")

# 1. Verify parcel
parcel = get_parcel(parcel_id)
print("\n--- Parcel ---")

if parcel:
    print(f"Parcel ID: {parcel.get('parcel_id')}")
    print(f"Status: {parcel.get('status')}")
    print(f"Weight: {parcel.get('weight_kg')} kg")
else:
    print("ERROR: Parcel not found.")

# 2. Verify courier capacity
courier = get_courier(courier_id)
print("\n--- Courier ---")

if courier:
    print(f"Courier: {courier.get('courier_id')}")
    print(f"Capacity: {courier.get('capacity_kg')} kg")
    print(f"Remaining: {courier.get('remaining_capacity_kg')} kg")
    print(f"Available: {courier.get('available')}")
else:
    print("ERROR: Courier not found.")

# 3. Verify allocation history
allocations = get_all_allocations()
print("\n--- Relevant Allocation Records ---")

records = [
    allocation
    for allocation in allocations
    if allocation.get("assignment_id") in {
        original_assignment_id,
        duplicate_assignment_id,
    }
]

for record in records:
    print(
        f"Assignment: {record.get('assignment_id')} | "
        f"Parcel: {record.get('parcel_id')} | "
        f"Status: {record.get('status')} | "
        f"Details: {record.get('details')}"
    )

original = next(
    (r for r in records if r.get("assignment_id") == original_assignment_id),
    None,
)

duplicate = next(
    (r for r in records if r.get("assignment_id") == duplicate_assignment_id),
    None,
)

print("\n========== CHECKS ==========")

checks = {
    "Parcel remains allocated": (
        parcel is not None and parcel.get("status") == "ALLOCATED"
    ),
    "Original assignment preserved": (
        original is not None and original.get("status") == "ALLOCATED"
    ),
    "Erroneous duplicate corrected": (
        duplicate is not None and duplicate.get("status") == "REJECTED"
    ),
    "Courier capacity restored": (
        courier is not None
        and abs(float(courier["remaining_capacity_kg"]) - 5.5) < 1e-9
    ),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {name}")

print(
    "\nRESULT:",
    "ALL CHECKS PASSED" if all(checks.values()) else "INVESTIGATION REQUIRED",
)
