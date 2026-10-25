
import asyncio
import json
import math

import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from services.database import (
    initialize_database,
    get_courier,
    save_courier,
)


class CourierAgent(spade.agent.Agent):

    def __init__(
        self,
        jid,
        password,
        courier_id,
        delivery_locations,
        capacity_kg,
    ):
        super().__init__(jid, password)

        self.courier_id = courier_id
        self.jid_string = str(jid)
        self.delivery_locations = list(delivery_locations)
        self.capacity_kg = float(capacity_kg)
        self.remaining_capacity_kg = float(capacity_kg)
        self.available = True

        # Track accepted assignments during this agent session.
        self.assigned_parcels = set()

    class ReceiveAssignmentBehaviour(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=10)

            if msg is None:
                return

            print("\n[COURIER] Assignment message received.")
            print(f"[COURIER] Sender: {msg.sender}")

            assignment_id = None
            parcel_id = "unknown"
            status = "REJECTED"
            details = "Assignment could not be processed."

            try:
                if msg.get_metadata("ontology") != "parcel-delivery":
                    raise ValueError("Unsupported message ontology.")

                if msg.get_metadata("performative") != "request":
                    raise ValueError("Expected an assignment request.")

                assignment = json.loads(msg.body)

                if not isinstance(assignment, dict):
                    raise ValueError("Assignment must be a JSON object.")

                assignment_id = assignment.get("assignment_id")
                parcel_id = str(assignment["parcel_id"])
                destination = assignment["delivery_location"]

                try:
                    weight = float(assignment["weight_kg"])
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        "Parcel weight must be a valid number."
                    ) from error

                if not assignment_id:
                    raise ValueError("Assignment ID is required.")

                if not math.isfinite(weight) or weight <= 0:
                    raise ValueError(
                        "Parcel weight must be a finite positive number."
                    )

                # Duplicate delivery requests must not deduct capacity twice.
                if parcel_id in self.agent.assigned_parcels:
                    status = "ACCEPTED"
                    details = "Parcel is already assigned to this courier."

                elif not self.agent.available:
                    status = "REJECTED"
                    details = "Courier is not available."

                elif destination not in self.agent.delivery_locations:
                    status = "REJECTED"
                    details = (
                        "Destination is outside the courier's service area."
                    )

                elif weight > self.agent.remaining_capacity_kg:
                    status = "REJECTED"
                    details = "Insufficient remaining capacity."

                else:
                    # Reserve capacity locally for this assignment.
                    self.agent.remaining_capacity_kg = max(
                        0.0,
                        self.agent.remaining_capacity_kg - weight,
                    )
                    self.agent.assigned_parcels.add(parcel_id)

                    if self.agent.remaining_capacity_kg <= 0:
                        self.agent.available = False

                    status = "ACCEPTED"
                    details = "Courier accepted the parcel assignment."

                print(f"[COURIER] Courier ID: {self.agent.courier_id}")
                print(f"[COURIER] Parcel ID: {parcel_id}")
                print(f"[COURIER] Status: {status}")
                print(f"[COURIER] Details: {details}")

            except (KeyError, TypeError, ValueError) as error:
                status = "REJECTED"
                details = str(error)
                print(f"[COURIER ERROR] Invalid assignment: {error}")

            except Exception as error:
                status = "REJECTED"
                details = "Unexpected error processing assignment."
                print(
                    f"[COURIER ERROR] {type(error).__name__}: {error}"
                )

            response_data = {
                "assignment_id": assignment_id,
                "parcel_id": parcel_id,
                "courier_id": self.agent.courier_id,
                "status": status,
                "details": details,
                "remaining_capacity_kg": (
                    self.agent.remaining_capacity_kg
                ),
            }

            response = Message(to=str(msg.sender).split("/")[0])
            response.set_metadata("performative", "inform")
            response.set_metadata("ontology", "parcel-delivery")
            response.set_metadata(
                "message_type",
                "assignment-response",
            )
            response.body = json.dumps(response_data)

            try:
                await self.send(response)
                print(f"[COURIER] Response sent to {msg.sender}.")
                print(
                    "[COURIER] Remaining capacity: "
                    f"{self.agent.remaining_capacity_kg} kg"
                )
            except Exception as error:
                print(
                    f"[COURIER ERROR] Could not send response: {error}"
                )

    async def setup(self):
        initialize_database()

        # Load the authoritative saved courier state.
        saved = get_courier(self.courier_id)

        if saved is None:
            # Create a database record only if one doesn't exist.
            courier_record = {
                "courier_id": self.courier_id,
                "jid": self.jid_string,
                "available": True,
                "capacity_kg": self.capacity_kg,
                "remaining_capacity_kg": self.capacity_kg,
                "delivery_locations": self.delivery_locations,
            }
            save_courier(courier_record)

            self.available = True
            self.remaining_capacity_kg = self.capacity_kg

        else:
            self.capacity_kg = float(saved["capacity_kg"])
            self.remaining_capacity_kg = float(
                saved["remaining_capacity_kg"]
            )
            self.available = bool(saved["available"])
            self.delivery_locations = list(
                saved["delivery_locations"]
            )

        print(f"[COURIER] Courier Agent {self.jid} started.")
        print(f"[COURIER] Courier ID: {self.courier_id}")
        print(f"[COURIER] Service locations: {self.delivery_locations}")
        print(f"[COURIER] Total capacity: {self.capacity_kg} kg")
        print(
            f"[COURIER] Remaining capacity: "
            f"{self.remaining_capacity_kg} kg"
        )
        print(f"[COURIER] Available: {self.available}")

        self.add_behaviour(self.ReceiveAssignmentBehaviour())

        print("[COURIER] Listening for assignments.")


async def main():
    courier = CourierAgent(
        jid="courier1@localhost",
        password="TestPassword123!",
        courier_id="C001",
        delivery_locations=["Colombo", "Kandy"],
        capacity_kg=10.0,
    )

    try:
        await courier.start(auto_register=True)

        print("[COURIER] Agent connected and ready.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[COURIER] Shutting down...")

    finally:
        if courier.is_alive():
            await courier.stop()


if __name__ == "__main__":
    asyncio.run(main())
