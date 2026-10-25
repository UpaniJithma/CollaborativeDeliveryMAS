
import math
from typing import Optional


def allocate_parcel(
    parcel: dict,
    couriers: list[dict],
) -> Optional[dict]:
    """
    Select the most suitable courier for a parcel.

    Allocation rules:
    1. Validate the parcel's required fields.
    2. Parcel weight must be a finite positive number.
    3. Courier must be available.
    4. Courier must serve the delivery location.
    5. Courier must have sufficient remaining capacity.
    6. Prefer the courier with the least remaining capacity
       after allocation (best-fit strategy).

    Returns:
        The selected courier dictionary, or None if no
        suitable courier is available.

    Raises:
        ValueError: If parcel data is invalid.
        TypeError: If parcel or couriers have invalid types.
    """

    # Validate input types.
    if not isinstance(parcel, dict):
        raise TypeError("Parcel must be a dictionary.")

    if not isinstance(couriers, list):
        raise TypeError("Couriers must be provided as a list.")

    # Validate required parcel fields.
    required_fields = [
        "parcel_id",
        "delivery_location",
        "weight_kg",
        "priority",
    ]

    missing = [
        field
        for field in required_fields
        if field not in parcel
    ]

    if missing:
        raise ValueError(
            "Parcel is missing required fields: "
            + ", ".join(missing)
        )

    # Validate parcel weight.
    try:
        weight = float(parcel["weight_kg"])
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Parcel weight must be a valid number."
        ) from error

    if not math.isfinite(weight) or weight <= 0:
        raise ValueError(
            "Parcel weight must be a finite number greater than zero."
        )

    # Validate delivery location.
    delivery_location = parcel["delivery_location"]

    if (
        not isinstance(delivery_location, str)
        or not delivery_location.strip()
    ):
        raise ValueError(
            "Parcel delivery location must be a non-empty string."
        )

    suitable_couriers = []

    # Evaluate each courier.
    for courier in couriers:

        if not isinstance(courier, dict):
            continue

        # Skip unavailable couriers.
        if not courier.get("available", False):
            continue

        # Check service locations.
        delivery_locations = courier.get(
            "delivery_locations", []
        )

        if not isinstance(delivery_locations, (list, tuple, set)):
            continue

        if delivery_location not in delivery_locations:
            continue

        # Validate remaining capacity.
        try:
            remaining_capacity = float(
                courier.get("remaining_capacity_kg", 0)
            )
        except (TypeError, ValueError):
            continue

        if (
            not math.isfinite(remaining_capacity)
            or remaining_capacity < 0
        ):
            continue

        # Reject couriers without sufficient capacity.
        if remaining_capacity < weight:
            continue

        # Best-fit: minimize unused capacity after allocation.
        remaining_after_allocation = remaining_capacity - weight

        suitable_couriers.append(
            (remaining_after_allocation, courier)
        )

    # No eligible courier was found.
    if not suitable_couriers:
        return None

    # Select the courier with the smallest remaining capacity.
    suitable_couriers.sort(
        key=lambda item: item[0]
    )

    selected_courier = suitable_couriers[0][1]

    return selected_courier
