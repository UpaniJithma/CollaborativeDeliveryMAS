
import asyncio
import json
import uuid

import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from services.allocation import allocate_parcel
from services.database import (
    initialize_database,
    get_courier,
    get_parcel,
    get_all_allocations,
    save_courier,
    save_allocation,
)


class CoordinatorAgent(spade.agent.Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)

        self.couriers = [
            {
                "courier_id": "C001",
                "jid": "courier1@localhost",
                "available": True,
                "delivery_locations": ["Colombo", "Kandy"],
                "capacity_kg": 10.0,
                "remaining_capacity_kg": 10.0,
            }
        ]

        self.processing_parcels = set()
        self.pending_responses = {}

    class AllocationBehaviour(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=10)

            if msg is None:
                return

            if msg.get_metadata("ontology") != "parcel-delivery":
                print("[COORDINATOR] Ignoring unsupported ontology.")
                return

            sender = str(msg.sender).split("/")[0]

            courier_jids = {
                courier["jid"]
                for courier in self.agent.couriers
            }

            # Route courier responses through the single listener.
            if sender in courier_jids:
                await self.handle_courier_response(msg)
                return

            if msg.get_metadata("performative") != "request":
                print(
                    f"[COORDINATOR] Ignoring message from {sender}: "
                    "unsupported performative."
                )
                return

            # Keep the listener available for courier responses.
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

                parcel_id = str(parcel["parcel_id"])

                if parcel_id in self.agent.processing_parcels:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "PROCESSING",
                        None,
                        "This parcel is already being processed.",
                    )
                    return

                # Confirm that the parcel exists in SQLite.
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
                    await self.process_allocation(
                        parcel,
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
                    f"[COORDINATOR ERROR] Invalid request: {error}"
                )

                try:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "REJECTED",
                        None,
                        str(error),
                    )
                except Exception as send_error:
                    print(
                        "[COORDINATOR ERROR] Could not send rejection: "
                        f"{send_error}"
                    )

            except Exception as error:
                print(
                    "[COORDINATOR ERROR] "
                    f"{type(error).__name__}: {error}"
                )

                try:
                    await self.send_result(
                        requester_jid,
                        parcel_id,
                        "ERROR",
                        None,
                        "An internal allocation error occurred.",
                    )
                except Exception as send_error:
                    print(
                        "[COORDINATOR ERROR] Could not send error "
                        f"response: {send_error}"
                    )

        async def process_allocation(self, parcel, requester_jid):
            parcel_id = str(parcel["parcel_id"])

            print(
                f"\n[COORDINATOR] Processing parcel {parcel_id}"
            )
            print(
                f"[COORDINATOR] Requester: {requester_jid}"
            )

            # DUPLICATE PROTECTION:
            # Check persistent allocation history before selecting
            # a courier or sending another assignment.
            existing_allocations = get_all_allocations()

            already_allocated = any(
                str(allocation.get("parcel_id")) == parcel_id
                and allocation.get("status") == "ALLOCATED"
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

            # Load persisted courier state without resetting capacity.
            for courier_record in self.agent.couriers:
                saved = get_courier(
                    courier_record["courier_id"]
                )

                if saved is None:
                    save_courier(courier_record)
                else:
                    courier_record["remaining_capacity_kg"] = float(
                        saved["remaining_capacity_kg"]
                    )
                    courier_record["available"] = bool(
                        saved["available"]
                    )
                    courier_record["capacity_kg"] = float(
                        saved["capacity_kg"]
                    )
                    courier_record["delivery_locations"] = list(
                        saved["delivery_locations"]
                    )

            courier = allocate_parcel(
                parcel,
                self.agent.couriers,
            )

            # No suitable courier: return a rejection.
            if courier is None:
                print(
                    f"[COORDINATOR] Result for {parcel_id}: "
                    "UNALLOCATED"
                )

                await self.send_result(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    "No suitable courier is available.",
                )
                return

            assignment_id = str(uuid.uuid4())

            assignment = dict(parcel)
            assignment["assignment_id"] = assignment_id
            assignment["courier_id"] = courier["courier_id"]

            # Save pending assignment before contacting the Courier.
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

            self.agent.pending_responses[assignment_id] = (
                response_future
            )

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
                    f"[COORDINATOR] Assignment {assignment_id} "
                    f"sent to {courier['courier_id']}."
                )

                try:
                    courier_result = await asyncio.wait_for(
                        response_future,
                        timeout=15,
                    )

                except asyncio.TimeoutError:
                    await self.record_and_reply(
                        requester_jid,
                        parcel_id,
                        "UNALLOCATED",
                        None,
                        "Courier response timed out.",
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

            # Validate the Courier's response.
            if (
                courier_result.get("parcel_id") != parcel_id
                or courier_result.get("assignment_id") != assignment_id
            ):
                await self.record_and_reply(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    "Courier response did not match the assignment.",
                    assignment_id,
                )
                return

            if courier_result.get("status") != "ACCEPTED":
                await self.record_and_reply(
                    requester_jid,
                    parcel_id,
                    "UNALLOCATED",
                    None,
                    courier_result.get(
                        "details",
                        "Courier rejected the assignment.",
                    ),
                    assignment_id,
                )
                return

            # Deduct capacity only after the Courier accepts.
            weight = float(parcel["weight_kg"])

            courier["remaining_capacity_kg"] = max(
                0.0,
                float(courier["remaining_capacity_kg"]) - weight,
            )

            if courier["remaining_capacity_kg"] <= 0:
                courier["available"] = False

            save_courier(courier)

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
                f"for {parcel_id} to {recipient}"
            )

            await self.send(response)

            print(
                f"[COORDINATOR] Response submitted for {parcel_id} "
                f"to {recipient}"
            )

    async def setup(self):
        initialize_database()

        print(f"[COORDINATOR] Agent {self.jid} started.")
        print("[COORDINATOR] SQLite database initialized.")

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
