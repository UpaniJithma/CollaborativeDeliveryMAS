
import json
import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# Database configuration
# ---------------------------------------------------------

DATABASE_PATH = (
    Path(__file__).resolve().parent.parent / "delivery_mas.db"
)


def get_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

def initialize_database():
    """Create tables and indexes if they do not exist."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS parcels (
                parcel_id TEXT PRIMARY KEY,
                sender_name TEXT NOT NULL,
                recipient_name TEXT NOT NULL,
                pickup_location TEXT NOT NULL,
                delivery_location TEXT NOT NULL,
                size TEXT NOT NULL,
                weight_kg REAL NOT NULL CHECK (weight_kg > 0),
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'REQUESTED',
                created_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                updated_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            );

            CREATE TABLE IF NOT EXISTS couriers (
                courier_id TEXT PRIMARY KEY,
                jid TEXT NOT NULL UNIQUE,
                available INTEGER NOT NULL DEFAULT 1
                    CHECK (available IN (0, 1)),
                capacity_kg REAL NOT NULL CHECK (capacity_kg >= 0),
                remaining_capacity_kg REAL NOT NULL
                    CHECK (
                        remaining_capacity_kg >= 0
                        AND remaining_capacity_kg <= capacity_kg
                    ),
                delivery_locations TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS allocations (
                assignment_id TEXT PRIMARY KEY,
                parcel_id TEXT NOT NULL,
                courier_id TEXT,
                status TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                updated_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                FOREIGN KEY (parcel_id)
                    REFERENCES parcels(parcel_id),
                FOREIGN KEY (courier_id)
                    REFERENCES couriers(courier_id)
            );

            CREATE INDEX IF NOT EXISTS idx_parcels_status
                ON parcels(status);

            CREATE INDEX IF NOT EXISTS idx_allocations_parcel
                ON allocations(parcel_id);

            CREATE INDEX IF NOT EXISTS idx_allocations_courier
                ON allocations(courier_id);
            """
        )


# ---------------------------------------------------------
# Parcel operations
# ---------------------------------------------------------

def save_parcel(parcel):
    """Insert a parcel or update the status of an existing parcel."""
    required_fields = [
        "parcel_id",
        "sender_name",
        "recipient_name",
        "pickup_location",
        "delivery_location",
        "size",
        "weight_kg",
        "priority",
    ]

    missing = [
        field for field in required_fields
        if field not in parcel
    ]

    if missing:
        raise ValueError(
            f"Parcel is missing fields: {', '.join(missing)}"
        )

    weight = float(parcel["weight_kg"])

    if weight <= 0:
        raise ValueError("Parcel weight must be greater than zero.")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO parcels (
                parcel_id,
                sender_name,
                recipient_name,
                pickup_location,
                delivery_location,
                size,
                weight_kg,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(parcel_id) DO UPDATE SET
                status = excluded.status,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (
                str(parcel["parcel_id"]),
                parcel["sender_name"],
                parcel["recipient_name"],
                parcel["pickup_location"],
                parcel["delivery_location"],
                parcel["size"],
                weight,
                parcel["priority"],
                parcel.get("status", "REQUESTED"),
            ),
        )


def update_parcel_status(parcel_id, status):
    """Update a parcel's current status."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE parcels
            SET status = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE parcel_id = ?
            """,
            (status, str(parcel_id)),
        )

        return cursor.rowcount > 0


def get_parcel(parcel_id):
    """Retrieve one parcel by ID."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM parcels WHERE parcel_id = ?",
            (str(parcel_id),),
        ).fetchone()

        return dict(row) if row else None


def get_all_parcels():
    """Retrieve all parcels, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM parcels ORDER BY created_at DESC"
        ).fetchall()

        return [dict(row) for row in rows]


# ---------------------------------------------------------
# Courier operations
# ---------------------------------------------------------

def save_courier(courier):
    """
    Insert or update a courier record.

    Required fields:
      courier_id, jid, capacity_kg, remaining_capacity_kg,
      delivery_locations

    The caller is responsible for preserving existing used
    capacity when updating a courier.
    """
    required_fields = [
        "courier_id",
        "jid",
        "capacity_kg",
        "remaining_capacity_kg",
        "delivery_locations",
    ]

    missing = [
        field for field in required_fields
        if field not in courier
    ]

    if missing:
        raise ValueError(
            f"Courier is missing fields: {', '.join(missing)}"
        )

    courier_id = str(courier["courier_id"]).strip().upper()
    jid = str(courier["jid"]).strip()

    if not courier_id:
        raise ValueError("Courier ID cannot be empty.")

    if not jid or "@" not in jid:
        raise ValueError("A valid XMPP JID is required.")

    capacity = float(courier["capacity_kg"])
    remaining = float(courier["remaining_capacity_kg"])

    if capacity < 0:
        raise ValueError("Courier capacity cannot be negative.")

    if remaining < 0 or remaining > capacity:
        raise ValueError(
            "Remaining capacity must be between zero "
            "and total capacity."
        )

    locations = courier["delivery_locations"]

    if not isinstance(locations, (list, tuple)):
        raise ValueError(
            "Delivery locations must be a list or tuple."
        )

    normalized_locations = []
    for location in locations:
        value = str(location).strip()
        if value and value not in normalized_locations:
            normalized_locations.append(value)

    if not normalized_locations:
        raise ValueError(
            "At least one delivery service area is required."
        )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO couriers (
                courier_id,
                jid,
                available,
                capacity_kg,
                remaining_capacity_kg,
                delivery_locations
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(courier_id) DO UPDATE SET
                jid = excluded.jid,
                available = excluded.available,
                capacity_kg = excluded.capacity_kg,
                remaining_capacity_kg =
                    excluded.remaining_capacity_kg,
                delivery_locations = excluded.delivery_locations
            """,
            (
                courier_id,
                jid,
                int(bool(courier.get("available", True))),
                capacity,
                remaining,
                json.dumps(normalized_locations),
            ),
        )


def get_courier(courier_id):
    """Retrieve one courier and deserialize service locations."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM couriers WHERE courier_id = ?",
            (str(courier_id).strip().upper(),),
        ).fetchone()

        if row is None:
            return None

        courier = dict(row)
        courier["available"] = bool(courier["available"])
        courier["delivery_locations"] = json.loads(
            courier["delivery_locations"]
        )

        return courier


def get_all_couriers():
    """Retrieve all couriers, ordered by courier ID."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM couriers ORDER BY courier_id"
        ).fetchall()

        couriers = []

        for row in rows:
            courier = dict(row)
            courier["available"] = bool(courier["available"])
            courier["delivery_locations"] = json.loads(
                courier["delivery_locations"]
            )
            couriers.append(courier)

        return couriers


def delete_courier(courier_id):
    """
    Delete a courier only when no allocation record references it.

    Returns:
        (True, message) on success.
        (False, message) when the courier cannot be deleted.
    """
    courier_id = str(courier_id).strip().upper()

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT courier_id
            FROM couriers
            WHERE courier_id = ?
            """,
            (courier_id,),
        ).fetchone()

        if existing is None:
            return False, "Courier not found."

        allocation = connection.execute(
            """
            SELECT assignment_id
            FROM allocations
            WHERE courier_id = ?
            LIMIT 1
            """,
            (courier_id,),
        ).fetchone()

        if allocation:
            return (
                False,
                "This courier has allocation history and cannot "
                "be deleted. Deactivate the courier instead.",
            )

        connection.execute(
            "DELETE FROM couriers WHERE courier_id = ?",
            (courier_id,),
        )

    return True, "Courier deleted successfully."


def set_courier_availability(courier_id, available):
    """Update a courier's database availability."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE couriers
            SET available = ?
            WHERE courier_id = ?
            """,
            (
                int(bool(available)),
                str(courier_id).strip().upper(),
            ),
        )

        return cursor.rowcount > 0


# ---------------------------------------------------------
# Allocation operations
# ---------------------------------------------------------

def save_allocation(
    assignment_id,
    parcel_id,
    courier_id,
    status,
    details="",
):
    """Insert or update an allocation record."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO allocations (
                assignment_id,
                parcel_id,
                courier_id,
                status,
                details
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET
                courier_id = excluded.courier_id,
                status = excluded.status,
                details = excluded.details,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (
                str(assignment_id),
                str(parcel_id),
                courier_id,
                status,
                details,
            ),
        )


def get_all_allocations():
    """Retrieve all allocation records, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM allocations
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]


def get_allocation(assignment_id):
    """Retrieve one allocation by assignment ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM allocations
            WHERE assignment_id = ?
            """,
            (str(assignment_id),),
        ).fetchone()

        return dict(row) if row else None
