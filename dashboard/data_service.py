
from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------
# Project path and existing database imports
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.database import (
    initialize_database,
    get_parcel,
    get_all_parcels,
    get_courier,
    get_all_couriers,
    get_all_allocations,
)


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

def initialize_data_service():
    """Initialize the existing SQLite database."""
    initialize_database()


# ---------------------------------------------------------
# Parcel data
# ---------------------------------------------------------

def fetch_parcels():
    """Return all registered parcels."""
    records = get_all_parcels()
    return records or []


def fetch_parcel(parcel_id):
    """Return one parcel by ID, or None if not found."""
    if not parcel_id:
        return None

    return get_parcel(str(parcel_id).strip())


def parcels_dataframe():
    """Return parcel records as a pandas DataFrame."""
    records = fetch_parcels()
    return pd.DataFrame(records) if records else pd.DataFrame()


# ---------------------------------------------------------
# Courier data
# ---------------------------------------------------------

def fetch_couriers():
    """Return all registered couriers."""
    records = get_all_couriers()
    return records or []


def fetch_courier(courier_id):
    """Return one courier by ID, or None if not found."""
    if not courier_id:
        return None

    return get_courier(str(courier_id).strip())


def couriers_dataframe():
    """Return courier records as a pandas DataFrame."""
    records = fetch_couriers()
    return pd.DataFrame(records) if records else pd.DataFrame()


# ---------------------------------------------------------
# Allocation data
# ---------------------------------------------------------

def fetch_allocations():
    """Return persisted allocation records."""
    records = get_all_allocations()
    return records or []


def allocations_dataframe():
    """Return allocation records as a pandas DataFrame."""
    records = fetch_allocations()
    return pd.DataFrame(records) if records else pd.DataFrame()


def fetch_parcel_allocations(parcel_id):
    """Return allocation records associated with one parcel."""
    if not parcel_id:
        return []

    parcel_id = str(parcel_id).strip()

    return [
        allocation
        for allocation in fetch_allocations()
        if str(allocation.get("parcel_id")) == parcel_id
    ]


# ---------------------------------------------------------
# Dashboard metrics
# ---------------------------------------------------------

def get_dashboard_metrics():
    """
    Calculate dashboard metrics from existing database records.

    These are display metrics only; they do not change
    parcel allocation or courier capacity.
    """
    parcels = fetch_parcels()
    couriers = fetch_couriers()
    allocations = fetch_allocations()

    allocated_parcel_ids = {
        str(record.get("parcel_id"))
        for record in allocations
        if record.get("status") == "ALLOCATED"
    }

    pending_statuses = {
        "REQUESTED",
        "PENDING",
        "REGISTERED",
    }

    allocated_count = sum(
        1
        for parcel in parcels
        if str(parcel.get("parcel_id")) in allocated_parcel_ids
    )

    pending_count = sum(
        1
        for parcel in parcels
        if str(parcel.get("status", "")).upper()
        in pending_statuses
        and str(parcel.get("parcel_id"))
        not in allocated_parcel_ids
    )

    unallocated_count = sum(
        1
        for parcel in parcels
        if str(parcel.get("status", "")).upper()
        in {"UNALLOCATED", "REJECTED"}
    )

    total_capacity = sum(
        _safe_float(courier.get("capacity_kg"))
        for courier in couriers
    )

    remaining_capacity = sum(
        _safe_float(courier.get("remaining_capacity_kg"))
        for courier in couriers
    )

    available_couriers = sum(
        1
        for courier in couriers
        if _is_available(courier.get("available"))
    )

    return {
        "total_parcels": len(parcels),
        "allocated_parcels": allocated_count,
        "pending_parcels": pending_count,
        "unallocated_parcels": unallocated_count,
        "total_couriers": len(couriers),
        "available_couriers": available_couriers,
        "total_capacity_kg": total_capacity,
        "remaining_capacity_kg": remaining_capacity,
        "used_capacity_kg": total_capacity - remaining_capacity,
    }


# ---------------------------------------------------------
# Courier capacity helpers
# ---------------------------------------------------------

def get_courier_capacity(courier):
    """Calculate used and remaining courier capacity."""
    capacity = _safe_float(courier.get("capacity_kg"))
    remaining = _safe_float(
        courier.get("remaining_capacity_kg")
    )

    used = capacity - remaining

    return {
        "capacity_kg": capacity,
        "remaining_capacity_kg": remaining,
        "used_capacity_kg": used,
        "utilisation_percent": (
            used / capacity * 100 if capacity > 0 else 0
        ),
    }


def _safe_float(value):
    """Convert a database value to float safely."""
    try:
        result = float(value)
        return result if pd.notna(result) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _is_available(value):
    """Interpret common SQLite boolean representations."""
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "available",
        }

    return bool(value)
