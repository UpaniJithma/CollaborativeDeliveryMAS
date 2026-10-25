
import asyncio
import json

import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from services.database import (
    initialize_database,
    save_parcel,
    update_parcel_status,
    get_parcel,
)


class ParcelHubAgent(spade.agent.Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.parcels = {}

    class ReceiveParcelBehaviour(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=10)

            if msg is None:
                return

            print("\n[HUB] Parcel message received.")
            print(f"[HUB] Sender: {msg.sender}")

            try:
                if (
                    msg.get_metadata("ontology")
                    != "parcel-delivery"
                ):
                    print("[HUB] Ignoring unsupported ontology.")
                    return

                if (
                    msg.get_metadata("performative")
                    != "request"
                ):
                    print("[HUB] Ignoring non-request message.")
                    return

                parcel = json.loads(msg.body)

                if not isinstance(parcel, dict):
                    raise ValueError(
                        "Parcel data must be a JSON object."
                    )

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
                    field
                    for field in required_fields
                    if field not in parcel
                ]

                if missing:
                    await self.send_response(
                        msg.sender,
                        parcel.get("parcel_id", "unknown"),
                        "REJECTED",
                        f"Missing fields: {', '.join(missing)}",
                    )
                    return

                parcel_id = str(parcel["parcel_id"])
                weight = float(parcel["weight_kg"])

                if weight <= 0:
                    raise ValueError(
                        "Parcel weight must be greater than zero."
                    )

                # Check the in-memory registry and SQLite.
                existing = self.agent.parcels.get(parcel_id)

                if existing is None:
                    existing = get_parcel(parcel_id)

                if existing is not None:
                    print(f"[HUB] Duplicate parcel: {parcel_id}")

                    await self.send_response(
                        msg.sender,
                        parcel_id,
                        existing["status"],
                        "Parcel has already been registered.",
                    )
                    return

                parcel["parcel_id"] = parcel_id
                parcel["weight_kg"] = weight
                parcel["status"] = "REGISTERED"

                # Persist before confirming registration.
                save_parcel(parcel)
                self.agent.parcels[parcel_id] = parcel

                print("[HUB] Parcel registered and saved.")
                print(f"[HUB] Parcel ID: {parcel_id}")
                print(
                    f"[HUB] Route: "
                    f"{parcel['pickup_location']} -> "
                    f"{parcel['delivery_location']}"
                )
                print(f"[HUB] Weight: {weight} kg")

                await self.send_response(
                    msg.sender,
                    parcel_id,
                    "REGISTERED",
                    "Parcel registered and saved successfully.",
                )

                # Forward the registered parcel to the Coordinator.
                await self.forward_to_coordinator(parcel)

            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ) as error:
                print(f"[HUB ERROR] Invalid parcel: {error}")

                await self.send_response(
                    msg.sender,
                    "unknown",
                    "REJECTED",
                    str(error),
                )

            except Exception as error:
                print(
                    "[HUB ERROR] Unexpected error: "
                    f"{type(error).__name__}: {error}"
                )

        async def forward_to_coordinator(self, parcel):
            coordinator_jid = "coordinator@localhost"

            request = Message(to=coordinator_jid)
            request.set_metadata("performative", "request")
            request.set_metadata("ontology", "parcel-delivery")
            request.set_metadata(
                "message_type",
                "allocation-request",
            )
            request.body = json.dumps(parcel)

            await self.send(request)

            print(
                f"[HUB] Parcel forwarded to Coordinator: "
                f"{parcel['parcel_id']}"
            )

            # Wait for the allocation result.
            response = await self.receive(timeout=15)

            if response is None:
                self.agent.parcels[parcel["parcel_id"]][
                    "status"
                ] = "ALLOCATION_PENDING"

                update_parcel_status(
                    parcel["parcel_id"],
                    "ALLOCATION_PENDING",
                )

                print(
                    "[HUB] Allocation result timed out for "
                    f"{parcel['parcel_id']}."
                )
                return

            if str(response.sender) != coordinator_jid:
                print(
                    "[HUB] Unexpected response sender: "
                    f"{response.sender}"
                )
                return

            try:
                result = json.loads(response.body)

                if result.get("parcel_id") != parcel["parcel_id"]:
                    print(
                        "[HUB] Received an allocation result "
                        "for another parcel."
                    )
                    return

                status = result.get(
                    "status",
                    "ALLOCATION_PENDING",
                )

                courier_id = result.get("courier_id")

                self.agent.parcels[parcel["parcel_id"]][
                    "status"
                ] = status

                self.agent.parcels[parcel["parcel_id"]][
                    "courier_id"
                ] = courier_id

                update_parcel_status(
                    parcel["parcel_id"],
                    status,
                )

                print(f"[HUB] Allocation status: {status}")
                print(f"[HUB] Assigned courier: {courier_id}")

            except (json.JSONDecodeError, TypeError, ValueError) as error:
                print(
                    f"[HUB ERROR] Invalid allocation result: {error}"
                )

        async def send_response(
            self,
            recipient_jid,
            parcel_id,
            status,
            details,
        ):
            response = Message(to=str(recipient_jid))
            response.set_metadata("performative", "inform")
            response.set_metadata("ontology", "parcel-delivery")

            response.body = json.dumps({
                "parcel_id": parcel_id,
                "status": status,
                "details": details,
            })

            await self.send(response)

            print(
                f"[HUB] Response sent to {recipient_jid}: {status}"
            )

    async def setup(self):
        initialize_database()

        print(f"[HUB] Parcel Hub Agent {self.jid} started.")
        print("[HUB] SQLite database initialized.")

        self.add_behaviour(
            self.ReceiveParcelBehaviour()
        )

        print("[HUB] Listening for parcel requests...")


async def main():
    hub = ParcelHubAgent(
        "hub@localhost",
        "TestPassword123!",
    )

    try:
        await hub.start(auto_register=True)

        print("[HUB] Agent connected and ready.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[HUB] Shutting down...")

    finally:
        if hub.is_alive():
            await hub.stop()


if __name__ == "__main__":
    asyncio.run(main())

