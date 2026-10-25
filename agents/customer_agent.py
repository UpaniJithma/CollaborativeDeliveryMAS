
import asyncio
import json
import uuid

import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message


class CustomerAgent(spade.agent.Agent):

    class SubmitParcelBehaviour(OneShotBehaviour):

        async def run(self):
            # Create a parcel request
            parcel = {
                "parcel_id": str(uuid.uuid4())[:8],
                "sender_name": "Test Sender",
                "recipient_name": "Test Recipient",
                "pickup_location": "Colombo",
                "delivery_location": "Kandy",
                "size": "medium",
                "weight_kg": 3.5,
                "priority": "high",
                "status": "REQUESTED",
            }

            # Send the request to the Hub Agent
            message = Message(to="hub@localhost")
            message.set_metadata("performative", "request")
            message.set_metadata("ontology", "parcel-delivery")
            message.body = json.dumps(parcel)

            await self.send(message)

            print(
                f"[CUSTOMER] Parcel request sent: "
                f"{parcel['parcel_id']}"
            )

            # Wait for the Hub's acknowledgement
            response = await self.receive(timeout=10)

            if response is None:
                print(
                    "[CUSTOMER] No response received "
                    "from the Hub within 10 seconds."
                )
                return

            try:
                result = json.loads(response.body)

                if not isinstance(result, dict):
                    raise ValueError(
                        "Hub response must be a JSON object."
                    )

                if (
                    response.get_metadata("ontology")
                    != "parcel-delivery"
                ):
                    print(
                        "[CUSTOMER] Received a message "
                        "with an unexpected ontology."
                    )
                    return

                if result.get("parcel_id") != parcel["parcel_id"]:
                    print(
                        "[CUSTOMER] Received a response "
                        "for a different parcel."
                    )
                    return

                status = result.get("status", "UNKNOWN")
                details = result.get("details", "No details provided.")

                if status == "REGISTERED":
                    print(
                        "[CUSTOMER] Hub confirmed parcel registration."
                    )
                else:
                    print(
                        "[CUSTOMER] Hub returned status: "
                        f"{status}"
                    )

                print(f"[CUSTOMER] Parcel ID: {result['parcel_id']}")
                print(f"[CUSTOMER] Details: {details}")

            except (json.JSONDecodeError, ValueError) as error:
                print(
                    "[CUSTOMER ERROR] Invalid Hub response: "
                    f"{error}"
                )

    async def setup(self):
        print(f"Customer Agent {self.jid} started.")
        self.add_behaviour(self.SubmitParcelBehaviour())


async def main():
    agent = CustomerAgent(
        "customer@localhost",
        "TestPassword123!",
    )

    try:
        await agent.start(auto_register=True)

        # Allow the one-shot behaviour to send and receive.
        await asyncio.sleep(12)

    finally:
        if agent.is_alive():
            await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
