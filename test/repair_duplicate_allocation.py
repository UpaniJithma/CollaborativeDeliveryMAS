
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path("delivery_mas.db")
DUPLICATE_ASSIGNMENT_ID = "ee840b33-a69d-45fd-9098-8b58189a1453"
ORIGINAL_ASSIGNMENT_ID = "5c9f263e-4711-4d10-bbde-181e7dd02c10"
PARCEL_ID = "79bc14c5"
COURIER_ID = "C001"

EXPECTED_CURRENT_CAPACITY = 2.0
RESTORED_CAPACITY = 5.5

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH.resolve()}")

# Keep a backup before changing anything.
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = DB_PATH.with_name(
    f"delivery_mas_before_repair_{timestamp}.db"
)
shutil.copy2(DB_PATH, backup_path)

conn = sqlite3.connect(DB_PATH, timeout=10)
conn.row_factory = sqlite3.Row

try:
    conn.execute("BEGIN IMMEDIATE")

    duplicate = conn.execute(
        """
        SELECT *
        FROM allocations
        WHERE assignment_id = ?
        """,
        (DUPLICATE_ASSIGNMENT_ID,),
    ).fetchone()

    original = conn.execute(
        """
        SELECT *
        FROM allocations
        WHERE assignment_id = ?
        """,
        (ORIGINAL_ASSIGNMENT_ID,),
    ).fetchone()

    courier = conn.execute(
        """
        SELECT *
        FROM couriers
        WHERE courier_id = ?
        """,
        (COURIER_ID,),
    ).fetchone()

    if not duplicate:
        raise RuntimeError("Expected duplicate allocation was not found.")

    if not original:
        raise RuntimeError("Original allocation was not found.")

    if (
        duplicate["parcel_id"] != PARCEL_ID
        or duplicate["courier_id"] != COURIER_ID
        or duplicate["status"] != "ALLOCATED"
    ):
        raise RuntimeError(
            "Duplicate record does not match the expected state. "
            "No changes were made."
        )

    if (
        original["parcel_id"] != PARCEL_ID
        or original["courier_id"] != COURIER_ID
        or original["status"] != "ALLOCATED"
    ):
        raise RuntimeError(
            "Original allocation is not in the expected state. "
            "No changes were made."
        )

    if not courier:
        raise RuntimeError("Courier C001 was not found.")

    if courier["remaining_capacity_kg"] != EXPECTED_CURRENT_CAPACITY:
        raise RuntimeError(
            f"Expected capacity {EXPECTED_CURRENT_CAPACITY} kg, "
            f"but found {courier['remaining_capacity_kg']} kg. "
            "No changes were made. Investigate any intervening allocations."
        )

    # Keep the erroneous row as an audit record, but stop treating it
    # as a successful allocation.
    conn.execute(
        """
        UPDATE allocations
        SET status = ?,
            details = ?,
            updated_at = ?
        WHERE assignment_id = ?
        """,
        (
            "REJECTED",
            "Duplicate test record corrected: parcel was already allocated "
            "by the original assignment; erroneous capacity deduction reversed.",
            datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            DUPLICATE_ASSIGNMENT_ID,
        ),
    )

    # Restore the verified capacity from before the duplicate test.
    conn.execute(
        """
        UPDATE couriers
        SET remaining_capacity_kg = ?
        WHERE courier_id = ?
        """,
        (RESTORED_CAPACITY, COURIER_ID),
    )

    conn.commit()

    print("\nDatabase repair completed.")
    print(f"Backup created: {backup_path}")

    print("\nCorrected duplicate allocation:")
    row = conn.execute(
        "SELECT * FROM allocations WHERE assignment_id = ?",
        (DUPLICATE_ASSIGNMENT_ID,),
    ).fetchone()
    print(dict(row))

    print("\nOriginal allocation preserved:")
    row = conn.execute(
        "SELECT * FROM allocations WHERE assignment_id = ?",
        (ORIGINAL_ASSIGNMENT_ID,),
    ).fetchone()
    print(dict(row))

    print("\nCourier C001 after repair:")
    row = conn.execute(
        "SELECT * FROM couriers WHERE courier_id = ?",
        (COURIER_ID,),
    ).fetchone()
    print(dict(row))

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
