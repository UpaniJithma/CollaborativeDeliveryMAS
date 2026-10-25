
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "delivery_mas.db"


def main():
    if not DATABASE_PATH.exists():
        print(f"ERROR: Database not found: {DATABASE_PATH}")
        return

    # Stop if the database is currently being used by the app or agents.
    print("\nCollaborativeDeliveryMAS - Test Data Reset")
    print("=" * 50)
    print(f"Database: {DATABASE_PATH}")

    print(
        "\nIMPORTANT: Stop Streamlit, the Coordinator Agent, "
        "the Courier Agent, and the XMPP server before continuing."
    )

    confirmation = input(
        "\nType RESET to back up the database and clear test records: "
    ).strip()

    if confirmation != "RESET":
        print("Reset cancelled. No records were changed.")
        return

    # Create a timestamped backup before making changes.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = PROJECT_ROOT / f"delivery_mas_backup_{timestamp}.db"

    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"\nBackup created: {backup_path.name}")

    db = sqlite3.connect(DATABASE_PATH, timeout=10)

    try:
        db.execute("PRAGMA foreign_keys = ON")
        cursor = db.cursor()

        # Verify the expected schema.
        tables = {
            row[0]
            for row in cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()
        }

        required_tables = {"parcels", "allocations", "couriers"}

        if not required_tables.issubset(tables):
            raise RuntimeError(
                f"Unexpected schema. Required tables: {required_tables}"
            )

        courier_columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(couriers)"
            ).fetchall()
        }

        if not {
            "capacity_kg",
            "remaining_capacity_kg",
            "available",
        }.issubset(courier_columns):
            raise RuntimeError(
                "Courier capacity columns do not match expectations."
            )

        # Show the current courier configuration.
        print("\nCourier configuration before reset:")

        couriers = cursor.execute("""
            SELECT courier_id, capacity_kg, remaining_capacity_kg,
                   available
            FROM couriers
        """).fetchall()

        for courier in couriers:
            print(
                f"  {courier[0]} | total={courier[1]} kg | "
                f"remaining={courier[2]} kg | available={courier[3]}"
            )

        # Preserve the database structure and courier registrations.
        db.execute("BEGIN IMMEDIATE")

        old_allocations = cursor.execute(
            "SELECT COUNT(*) FROM allocations"
        ).fetchone()[0]

        old_parcels = cursor.execute(
            "SELECT COUNT(*) FROM parcels"
        ).fetchone()[0]

        # Remove dependent records before parent parcel records.
        cursor.execute("DELETE FROM allocations")
        cursor.execute("DELETE FROM parcels")

        # Restore each courier's full configured capacity.
        cursor.execute("""
            UPDATE couriers
            SET remaining_capacity_kg = capacity_kg,
                available = 1
        """)

        db.commit()

        print("\nRESET COMPLETED")
        print(f"  Allocation records removed: {old_allocations}")
        print(f"  Parcel records removed: {old_parcels}")

        print("\nDatabase verification:")

        for table in ("parcels", "allocations", "couriers"):
            count = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"  {table}: {count} records")

        print("\nCourier capacity after reset:")

        couriers = cursor.execute("""
            SELECT courier_id, capacity_kg, remaining_capacity_kg,
                   available
            FROM couriers
        """).fetchall()

        for courier in couriers:
            print(
                f"  {courier[0]} | total={courier[1]} kg | "
                f"remaining={courier[2]} kg | available={courier[3]}"
            )

        print(f"\nBackup preserved at: {backup_path}")

    except Exception:
        db.rollback()
        print("\nERROR: Reset failed. Database changes were rolled back.")
        print(f"Your backup is preserved at: {backup_path}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
