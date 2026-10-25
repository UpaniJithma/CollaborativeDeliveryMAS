
import asyncio
import json

import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template

from services.database import initialize_database, get_parcel


class AllocationTestAgent(spade.agent.Agent):

    class TestBehaviour(OneShotBehaviour):

        async def run(self):
            parcel_id = "79bc14c5"
            parcel = get_parcel(parcel_id)

            if parcel is None:
                print(f"[TEST] ERROR: Parcel {parcel_id} not found.")
                return

            print(f"[TEST] Existing parcel: {parcel_id}")
            print(f"[TEST] Status: {parcel.get('status')}")
            print("[TEST] Sending duplicate request to Coordinator.")

            request = Message(to="coordinator@localhost")
            request.set_metadata("performative", "request")
            request.set_metadata("ontology", "parcel-delivery")
            request.body = json.dumps(parcel)

            await self.send(request)
            print("[TEST] Request sent. Waiting for response...")

            # Only accept a response from the Coordinator.
            template = Template()
            template.set_metadata("ontology", "parcel-delivery")
            template.set_metadata("performative", "inform")

            deadline = asyncio.get_running_loop().time() + 30

            while asyncio.get_running_loop().time() < deadline:
                remaining = deadline - asyncio.get_running_loop().time()
                response = await self.receive(timeout=remaining)

                if response is None:
                    break

                sender = str(response.sender).split("/")[0]
                if sender != "coordinator@localhost":
                    print(f"[TEST] Ignoring message from {sender}")
                    continue

                try:
                    result = json.loads(response.body)
                except (json.JSONDecodeError, TypeError):
                    print(f"[TEST] Invalid JSON response: {response.body}")
                    continue

                print("[TEST] Coordinator response:")
                print(json.dumps(result, indent=2))

                status = result.get("status")
                if status == "ALREADY_ALLOCATED":
                    print("[TEST] PASS: Duplicate allocation was blocked.")
                elif status == "ALLOCATED":
                    print("[TEST] FAIL: Duplicate allocation was reported as allocated.")
                else:
                    print(f"[TEST] Received status: {status}")
                return

            print("[TEST] FAIL: No Coordinator response received in 30 seconds.")

    async def setup(self):
        print(f"[TEST] Agent started: {self.jid}")
        self.add_behaviour(self.TestBehaviour())


async def main():
    initialize_database()

    agent = AllocationTestAgent(
        "allocationtest@localhost",
        "TestPassword123!",
    )

    try:
        await agent.start(auto_register=True)
        print("[TEST] Running duplicate allocation test...")
        await asyncio.sleep(32)
    except Exception as error:
        print(f"[TEST] Agent error: {type(error).__name__}: {error}")
    finally:
        if agent.is_alive():
            await agent.stop()
            print("[TEST] Agent stopped.")


if __name__ == "__main__":
    asyncio.run(main())
