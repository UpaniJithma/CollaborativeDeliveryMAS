
import asyncio
import json
import uuid

import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message

from services.database import (
    initialize_database,
    save_parcel,
    get_parcel,
    get_courier,
    get_all_allocations,
)


COORDINATOR_JID = "coordinator@localhost"
COURIER_ID = "C001"

EXPECTED_CAPACITY_BEFORE = 4.5
TEST_WEIGHT_KG = 1.0
EXPECTED_CAPACITY_AFTER = 3.5

RESPONSE_TIMEOUT_SECONDS = 25


class IntegrationTestAgent(spade.agent.Agent):

    class TestBehaviour(OneShotBehaviour):

        async def run(self):
            parcel_id = f"INT-{uuid.uuid4().hex[:10].upper()}"

            parcel = {
                "parcel_id": parcel_id,
                "sender_name": "Integration Test Sender",
                "recipient_name": "Integration Test Recipient",
                "pickup_location": "Colombo",
                "delivery_location": "Kandy",
                "size": "Small",
                "weight_kg": TEST_WEIGHT_KG,
                "priority": "normal",
                "status": "REQUESTED",
            }

            print("\n========== INTEGRATION TEST ==========")
            print(f"Parcel ID: {parcel_id}")

            # 1. Check the courier's initial persisted capacity.
            courier_before = get_courier(COURIER_ID)

            if courier_before is None:
                print("[FAIL] Courier C001 is not registered.")
                return

            capacity_before = float(
                courier_before["remaining_capacity_kg"]
            )

            print(f"Capacity before: {capacity_before} kg")

            if abs(
                capacity_before - EXPECTED_CAPACITY_BEFORE
            ) > 1e-9:
                print(
                    "[STOP] Expected capacity was "
                    f"{EXPECTED_CAPACITY_BEFORE} kg, but found "
                    f"{capacity_before} kg."
                )
                print(
                    "[STOP] No test parcel was created or submitted."
                )
                return

            # 2. Register a fresh parcel in SQLite.
            save_parcel(parcel)
            print("[TEST] New parcel registered in SQLite.")

            # 3. Send the allocation request to the Coordinator.
            request = Message(to=COORDINATOR_JID)
            request.set_metadata("performative", "request")
            request.set_metadata("ontology", "parcel-delivery")
            request.body = json.dumps(parcel)

            try:
                await self.send(request)
            except Exception as error:
                print(
                    f"[FAIL] Could not send allocation request: {error}"
                )
                return

            print("[TEST] Request sent to Coordinator.")
            print("[TEST] Waiting for allocation result...")

            # 4. Wait for the matching Coordinator response.
            # SPADE receive() does not accept template=.
            deadline = (
                asyncio.get_running_loop().time()
                + RESPONSE_TIMEOUT_SECONDS
            )

            result = None

            while True:
                remaining = (
                    deadline - asyncio.get_running_loop().time()
                )

                if remaining <= 0:
                    break

                try:
                    response = await self.receive(
                        timeout=min(5, remaining)
                    )
                except Exception as error:
                    print(
                        "[FAIL] Error receiving response: "
                        f"{error}"
                    )
                    return

                if response is None:
                    continue

                sender = (
                    str(response.sender).split("/")[0].lower()
                    if response.sender
                    else ""
                )

                if sender != COORDINATOR_JID.lower():
                    print(
                        "[TEST] Ignoring message from "
                        f"{sender or 'unknown'}."
                    )
                    continue

                if (
                    response.get_metadata("ontology")
                    != "parcel-delivery"
                    or response.get_metadata("performative")
                    != "inform"
                ):
                    print(
                        "[TEST] Ignoring non-allocation response "
                        "from Coordinator."
                    )
                    continue

                try:
                    candidate = json.loads(response.body)
                except (json.JSONDecodeError, TypeError):
                    print("[TEST] Ignoring invalid JSON response.")
                    continue

                if candidate.get("parcel_id") != parcel_id:
                    print(
                        "[TEST] Ignoring response for another parcel: "
                        f"{candidate.get('parcel_id')}"
                    )
                    continue

                result = candidate
                break

            if result is None:
                print(
                    "[FAIL] No matching Coordinator response received "
                    f"within {RESPONSE_TIMEOUT_SECONDS} seconds."
                )
                print(
                    "[CHECK] Inspect the Coordinator and Courier "
                    "terminals and database before retrying."
                )
                print(
                    "[WARNING] The request may already have been "
                    "processed. Do not blindly rerun this test."
                )
                return

            print("\n[TEST] Coordinator result:")
            print(json.dumps(result, indent=2))

            # 5. Read the persisted database state.
            courier_after = get_courier(COURIER_ID)
            stored_parcel = get_parcel(parcel_id)

            allocations = [
                allocation
                for allocation in get_all_allocations()
                if str(allocation.get("parcel_id")) == parcel_id
            ]

            allocated_records = [
                allocation
                for allocation in allocations
                if allocation.get("status") == "ALLOCATED"
            ]

            print("\n========== VERIFICATION ==========")

            # Check 1: Successful Coordinator response.
            status_ok = result.get("status") == "ALLOCATED"

            print(
                f"{'PASS' if status_ok else 'FAIL'}: "
                "Coordinator returned ALLOCATED"
            )

            # Check 2: Exactly one successful allocation.
            allocation_ok = len(allocated_records) == 1

            print(
                f"{'PASS' if allocation_ok else 'FAIL'}: "
                "Exactly one successful allocation record exists"
            )

            # Check 3: Persisted capacity decreased by exactly 1 kg.
            capacity_ok = False

            if courier_after is not None:
                capacity_after = float(
                    courier_after["remaining_capacity_kg"]
                )

                print(f"Capacity after: {capacity_after} kg")

                capacity_ok = (
                    abs(
                        capacity_after
                        - (capacity_before - TEST_WEIGHT_KG)
                    ) < 1e-9
                    and abs(
                        capacity_after - EXPECTED_CAPACITY_AFTER
                    ) < 1e-9
                )

                print(
                    f"{'PASS' if capacity_ok else 'FAIL'}: "
                    "Persisted capacity decreased by exactly 1.0 kg"
                )
            else:
                print("[FAIL] Courier record disappeared.")

            # Check 4: Parcel remains registered.
            parcel_ok = stored_parcel is not None

            print(
                f"{'PASS' if parcel_ok else 'FAIL'}: "
                "Test parcel remains registered in SQLite"
            )

            # Check 5: Allocation references the expected courier.
            courier_assignment_ok = (
                len(allocated_records) == 1
                and allocated_records[0].get("courier_id")
                == COURIER_ID
                and result.get("courier_id") == COURIER_ID
            )

            print(
                f"{'PASS' if courier_assignment_ok else 'FAIL'}: "
                f"Parcel assigned to {COURIER_ID}"
            )

            all_passed = all(
                [
                    status_ok,
                    allocation_ok,
                    capacity_ok,
                    parcel_ok,
                    courier_assignment_ok,
                ]
            )

            print("\n===================================")
            print(
                "RESULT: "
                + (
                    "ALL CHECKS PASSED"
                    if all_passed
                    else "CHECKS FAILED"
                )
            )

            if not all_passed:
                print(
                    "[WARNING] Investigate the failed check and "
                    "database state before running another test."
                )

    async def setup(self):
        print(f"[TEST] Integration agent started: {self.jid}")
        self.add_behaviour(self.TestBehaviour())


async def main():
    initialize_database()

    agent = IntegrationTestAgent(
        "integrationtest@localhost",
        "TestPassword123!",
    )

    try:
        await agent.start(auto_register=True)

        print(
            "[TEST] Running Coordinator-Courier integration test."
        )

        # Allow the behaviour time to finish.
        await asyncio.sleep(RESPONSE_TIMEOUT_SECONDS + 5)

    except Exception as error:
        print(
            f"[TEST ERROR] {type(error).__name__}: {error}"
        )

    finally:
        if agent.is_alive():
            await agent.stop()
            print("[TEST] Integration agent stopped.")


if __name__ == "__main__":
    asyncio.run(main())
