
import sqlite3

DB_PATH = "delivery_mas.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== DATABASE TABLES ===")
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""")

for row in cursor.fetchall():
    print(f"\nTable: {row['name']}")

    cursor.execute(f"PRAGMA table_info('{row['name']}')")
    for column in cursor.fetchall():
        print(
            f"  {column['name']} "
            f"({column['type']})"
        )

print("\n=== DUPLICATE ALLOCATION RECORD ===")
cursor.execute("""
    SELECT *
    FROM allocations
    WHERE assignment_id = ?
""", ("ee840b33-a69d-45fd-9098-8b58189a1453",))

row = cursor.fetchone()
print(dict(row) if row else "Record not found")

print("\n=== COURIER C001 ===")
cursor.execute("""
    SELECT *
    FROM couriers
    WHERE courier_id = ?
""", ("C001",))

row = cursor.fetchone()
print(dict(row) if row else "Courier not found")

conn.close()
