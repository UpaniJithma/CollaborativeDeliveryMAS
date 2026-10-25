
import asyncio
import json
import uuid
import traceback

import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from services.allocation import allocate_parcel
from services.database import (
    initialize_database,
    get_all_couriers,
    get_courier,
    get_parcel,
    get_all_allocations,
    save_courier,
    save_allocation,
)


class CoordinatorAgent(spade.agent.Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)

        # Populated from SQLite during setup and refreshed before allocation.
        self.couriers = []

        self.processing_parcels = set()
        self.pending_responses = {}

    def refresh_couriers(self):
        """Load all registered couriers and preserve their saved state."""
        database_couriers = get_all_couriers()

        self.couriers = []

        for saved in database_couriers:
            courier = dict(saved)

            courier["courier_id"] = str(
                courier["courier_id"]
            ).strip().upper()

            courier["jid"] = str(courier["jid"]).strip()
            courier["available"] = bool(courier["available"])
            courier["capacity_kg"] = float(courier["capacity_kg"])
            courier["remaining_capacity_kg"] = float(
                courier["remaining_capacity_kg"]
            )
            courier["delivery_locations"] = list(
                courier["delivery_locations"]
            )

            self.couriers.append(courier)

        print(
            f"[COORDINATOR] Loaded {len(self.couriers)} "
            "registered courier(s)."
        )

        for courier in self.couriers:
            print(
                f"  ID={courier['courier_id']}, "
                f"JID={courier['jid']}, "
                f"Available={courier['available']}, "
                f"Capacity={courier['remaining_capacity_kg']} kg, "
                f"Locations={courier['delivery_locations']}"
            )

    class AllocationBehaviour(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=10)

            if msg is None:
                return

            if msg.get_metadata("ontology") != "parcel-delivery":
                print("[COORDINATOR] Ignoring unsupported ontology.")
                return

            sender = str(msg.sender).split("/")[0]

            # Use the latest courier list to recognize courier responses.
            courier_jids = {
                str(courier["jid"]).split("/")[0]
                for courier in self.agent.couriers
            }

            if sender in courier_jids:
                await self.handle_courier_response(msg)
                return

            if msg.get_metadata("performative") != "request":
                print(
                    f"[COORDINATOR] Ignoring message from {sender}: "
                    "unsupported performative."
                )
                return

            # Keep this listener free to receive courier responses.
            asyncio.create_task(
                self.handle_allocation_request(msg)
            )

        async def handle_courier_response(self, msg):
            try:
                result = json.loads(msg.body)

                if not isinstance(result, dict):
                    raise ValueError(
                        "Courier response must be a JSON object."
                    )

            except (json.JSONDecodeError, TypeError, ValueError) as error:
                print(
                    f"[COORDINATOR] Invalid courier response: {error}"
                )
                return

            assignment_id = result.get("assignment_id")

            if not assignment_id:
                print(
                    "[COORDINATOR] Courier response has no assignment ID."
                )
                return

            future = self.agent.pending_responses.get(assignment_id)

            if future is None:
                print(
                    "[COORDINATOR] No pending assignment matches "
                    f"{assignment_id}."
                )
                return

            if not future.done():
                future.set_result(result)
                print(
                    "[COORDINATOR] Courier response received for "
                    f"assignment {assignment_id}."
                )

        async def handle_allocation_request(self, msg):
            parcel_id = "unknown"
            requester_jid = str(msg.sender).split("/")[0]

            try:
                parcel = json.loads(msg.body)

                if not isinstance(parcel, dict):
                    raise ValueError(
                        "Parcel request must be a JSON object."
                    )

                if not parcel.get("parcel_id"):
                    raise ValueError("Parcel ID is required.")

                parcel_id = str(parcel["parcel_id"]).strip()

                if parcel_id in self.agent.processing_parcels:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "PROCESSING",
                        None,
                        "This parcel is already being processed.",
                    )
                    return

                stored_parcel = get_parcel(parcel_id)

                if stored_parcel is None:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "REJECTED",
                        None,
                        "Parcel is not registered in the database.",
                    )
                    return

                self.agent.processing_parcels.add(parcel_id)

                try:
                    # Use the persisted parcel as the authoritative source.
                    await self.process_allocation(
                        stored_parcel,
                        requester_jid,
                    )
                finally:
                    self.agent.processing_parcels.discard(parcel_id)

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                print(
                    f"[COORDINATOR ERROR] Invalid request: "
                    f"{type(error).__name__}: {error}"
                )

                try:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "REJECTED",
                        None,
                        str(error),
                    )
                except Exception:
                    print(
                        "[COORDINATOR ERROR] Could not send rejection:"
                    )
                    traceback.print_exc()

            except Exception as error:
                print(
                    "[COORDINATOR ERROR] Unexpected allocation-request "
                    f"failure: {type(error).__name__}: {error}"
                )
                traceback.print_exc()

                try:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "ERROR",
                        None,
                        f"{type(error).__name__}: {error}",
                    )
                except Exception:
                    print(
                        "[COORDINATOR ERROR] Could not send error response:"
                    )
                    traceback.print_exc()

        async def process_allocation(self, parcel, requester_jid):
            parcel_id = str(parcel["parcel_id"]).strip()

            print(
                f"\n[COORDINATOR] Processing parcel {parcel_id}"
            )
            print(
                f"[COORDINATOR] Requester: {requester_jid}"
            )

            # Block duplicate successful allocations.
            existing_allocations = get_all_allocations()

            already_allocated = any(
                str(allocation.get("parcel_id")) == parcel_id
                and str(allocation.get("status", "")).upper()
                == "ALLOCATED"
                for allocation in existing_allocations
            )

            if already_allocated:
                print(
                    f"[COORDINATOR] Duplicate allocation blocked "
                    f"for parcel {parcel_id}."
                )

                await self.send_result(
                    requester_jid,
                    parcel_id,
                    "ALREADY_ALLOCATED",
                    None,
                    "This parcel has already been allocated.",
                )
                return

            # Refresh the list so every registered courier is considered.
            self.agent.refresh_couriers()

            if not self.agent.couriers:
                print(
                    "[COORDINATOR] No couriers are registered in SQLite."
                )

                await self.send_result(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    "No couriers are registered in the database.",
                )
                return

            print(
                f"[COORDINATOR] Destination: "
                f"{parcel.get('delivery_location')}"
            )
            print(
                f"[COORDINATOR] Parcel weight: "
                f"{parcel.get('weight_kg')} kg"
            )

            for courier_record in self.agent.couriers:
                print(
                    f"[COORDINATOR] Candidate {courier_record['courier_id']}: "
                    f"available={courier_record['available']}, "
                    f"remaining={courier_record['remaining_capacity_kg']} kg, "
                    f"locations={courier_record['delivery_locations']}"
                )

            courier = allocate_parcel(
                parcel,
                self.agent.couriers,
            )

            if courier is None:
                print(
                    f"[COORDINATOR] No eligible courier for {parcel_id}."
                )

                await self.send_result(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    "No suitable courier is available. Check service "
                    "area, availability, and remaining capacity.",
                )
                return

            assignment_id = str(uuid.uuid4())

            assignment = dict(parcel)
            assignment["assignment_id"] = assignment_id
            assignment["courier_id"] = courier["courier_id"]

            print(
                f"[COORDINATOR] Selected courier "
                f"{courier['courier_id']} ({courier['jid']})."
            )

            # Persist the pending assignment before contacting the courier.
            save_allocation(
                assignment_id=assignment_id,
                parcel_id=parcel_id,
                courier_id=courier["courier_id"],
                status="PENDING",
                details="Waiting for courier confirmation.",
            )

            response_future = (
                asyncio.get_running_loop().create_future()
            )
            self.agent.pending_responses[assignment_id] = response_future

            try:
                request = Message(to=courier["jid"])
                request.set_metadata("performative", "request")
                request.set_metadata("ontology", "parcel-delivery")
                request.set_metadata(
                    "message_type",
                    "courier-assignment",
                )
                request.body = json.dumps(assignment)

                await self.send(request)

                print(
                    f"[COORDINATOR] Assignment {assignment_id} sent "
                    f"to {courier['courier_id']}."
                )

                try:
                    courier_result = await asyncio.wait_for(
                        response_future,
                        timeout=15,
                    )
                except asyncio.TimeoutError:
                    print(
                        f"[COORDINATOR] Timeout waiting for "
                        f"{courier['courier_id']}."
                    )

                    await self.record_and_reply(
                        requester_jid,
                        parcel_id,
                        "UNALLOCATED",
                        None,
                        f"Courier {courier['courier_id']} did not respond "
                        "within 15 seconds.",
                        assignment_id,
                    )
                    return

            finally:
                self.agent.pending_responses.pop(
                    assignment_id,
                    None,
                )

                if not response_future.done():
                    response_future.cancel()

            # Validate that the reply belongs to this assignment.
            if (
                str(courier_result.get("parcel_id")) != parcel_id
                or str(courier_result.get("assignment_id"))
                != assignment_id
                or str(courier_result.get("courier_id"))
                != str(courier["courier_id"])
            ):
                print(
                    "[COORDINATOR] Courier response did not match "
                    "the pending assignment."
                )

                await self.record_and_reply(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    "Courier response did not match the assignment.",
                    assignment_id,
                )
                return

            if str(courier_result.get("status", "")).upper() != "ACCEPTED":
                details = courier_result.get(
                    "details",
                    "Courier rejected the assignment.",
                )

                print(
                    f"[COORDINATOR] Courier rejected assignment: {details}"
                )

                await self.record_and_reply(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    details,
                    assignment_id,
                )
                return

            # Reload state before updating to avoid relying on stale values.
            saved_courier = get_courier(courier["courier_id"])

            if saved_courier is None:
                raise RuntimeError(
                    f"Courier {courier['courier_id']} disappeared "
                    "from the database."
                )

            weight = float(parcel["weight_kg"])
            remaining = float(
                saved_courier["remaining_capacity_kg"]
            )

            # The courier agent has accepted; persist the capacity update.
            new_remaining = max(0.0, remaining - weight)

            saved_courier["remaining_capacity_kg"] = new_remaining
            saved_courier["available"] = (
                bool(saved_courier["available"])
                and new_remaining > 0
            )

            save_courier(saved_courier)

            # Keep the in-memory courier consistent with SQLite.
            courier["remaining_capacity_kg"] = new_remaining
            courier["available"] = saved_courier["available"]

            await self.record_and_reply(
                requester_jid,
                parcel_id,
                "ALLOCATED",
                courier["courier_id"],
                courier_result.get(
                    "details",
                    "Courier accepted the assignment.",
                ),
                assignment_id,
            )

            print(
                f"[COORDINATOR] Parcel {parcel_id} allocated to "
                f"{courier['courier_id']}."
            )

        async def record_and_reply(
            self,
            requester_jid,
            parcel_id,
            status,
            courier_id,
            details,
            assignment_id=None,
        ):
            if assignment_id is not None:
                save_allocation(
                    assignment_id=assignment_id,
                    parcel_id=parcel_id,
                    courier_id=courier_id,
                    status=status,
                    details=details,
                )

            await self.send_result(
                requester_jid,
                parcel_id,
                status,
                courier_id,
                details,
            )

        async def send_result(
            self,
            recipient_jid,
            parcel_id,
            status,
            courier_id,
            details,
        ):
            recipient = str(recipient_jid).split("/")[0]

            response = Message(to=recipient)
            response.set_metadata("performative", "inform")
            response.set_metadata("ontology", "parcel-delivery")

            response.body = json.dumps(
                {
                    "parcel_id": parcel_id,
                    "status": status,
                    "courier_id": courier_id,
                    "details": details,
                }
            )

            print(
                f"[COORDINATOR] Sending {status} response "
                f"for {parcel_id} to {recipient}: {details}"
            )

            await self.send(response)

            print(
                f"[COORDINATOR] Response sent for {parcel_id} "
                f"to {recipient}."
            )

    async def setup(self):
        initialize_database()

        print(f"[COORDINATOR] Agent {self.jid} started.")
        print("[COORDINATOR] SQLite database initialized.")

        self.refresh_couriers()

        self.add_behaviour(self.AllocationBehaviour())

        print("[COORDINATOR] Listening for allocation requests.")


async def main():
    coordinator = CoordinatorAgent(
        "coordinator@localhost",
        "TestPassword123!",
    )

    try:
        await coordinator.start(auto_register=True)

        print("[COORDINATOR] Agent connected and ready.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[COORDINATOR] Shutting down...")

    finally:
        if coordinator.is_alive():
            await coordinator.stop()


if __name__ == "__main__":
    asyncio.run(main())
