
from services.database import (
    initialize_database,
    get_all_allocations,
    get_courier,
)

initialize_database()

print("ALLOCATION RECORDS")
for allocation in get_all_allocations():
    print(allocation)

print("\nCOURIER C001")
print(get_courier("C001"))

