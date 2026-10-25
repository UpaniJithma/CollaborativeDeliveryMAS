
import asyncio
import json
import uuid

import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template


class CourierTestAgent(spade.agent.Agent):

    class TestBehaviour(OneShotBehaviour):

        async def run(self):
            # Unique test ID avoids reusing TEST2001 on every run.
            assignment_id = str(uuid.uuid4())

            assignment = {
                "assignment_id": assignment_id,
                "parcel_id": f"COURIER-TEST-{assignment_id[:8]}",
                "courier_id": "C001",
                "delivery_location": "Kandy",
                "weight_kg": 1.0,
                "priority": "normal",
            }

            request = Message(to="courier1@localhost")
            request.set_metadata("performative", "request")
            request.set_metadata("ontology", "parcel-delivery")
            request.set_metadata("message_type", "courier-assignment")
            request.body = json.dumps(assignment)

            await self.send(request)
            print("[TEST] Assignment sent to Courier C001.")
            print(f"[TEST] Parcel ID: {assignment['parcel_id']}")
            print(f"[TEST] Assignment ID: {assignment_id}")

            template = Template()
            template.set_metadata("ontology", "parcel-delivery")

            response = await self.receive(
                timeout=15,
                template=template,
            )

            if response is None:
                print("[TEST] FAIL: No response received from Courier.")
                return

            try:
                result = json.loads(response.body)
            except (json.JSONDecodeError, TypeError):
                print(f"[TEST] FAIL: Invalid JSON: {response.body}")
                return

            print("[TEST] Courier response:")
            print(json.dumps(result, indent=2))

            if result.get("assignment_id") != assignment_id:
                print("[TEST] FAIL: Assignment ID mismatch.")
                return

            if result.get("parcel_id") != assignment["parcel_id"]:
                print("[TEST] FAIL: Parcel ID mismatch.")
                return

            if result.get("status") == "ACCEPTED":
                print("[TEST] PASS: Courier accepted the assignment.")
            else:
                print(
                    "[TEST] Courier did not accept the assignment: "
                    f"{result.get('status')}"
                )

    async def setup(self):
        self.add_behaviour(self.TestBehaviour())


async def main():
    agent = CourierTestAgent(
        "couriertest@localhost",
        "TestPassword123!",
    )

    try:
        await agent.start(auto_register=True)
        print("[TEST] Courier communication test running.")
        await asyncio.sleep(18)
    except Exception as error:
        print(f"[TEST] ERROR: {type(error).__name__}: {error}")
    finally:
        if agent.is_alive():
            await agent.stop()
            print("[TEST] Test agent stopped.")


if __name__ == "__main__":
    asyncio.run(main())
