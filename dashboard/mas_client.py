
import asyncio
import json
import os
import uuid

import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message


COORDINATOR_JID = os.getenv(
    "MAS_COORDINATOR_JID",
    "coordinator@localhost",
)

XMPP_PASSWORD = os.getenv(
    "MAS_UI_XMPP_PASSWORD",
    "TestPassword123!",
)

RESPONSE_TIMEOUT_SECONDS = 25


class AllocationRequestAgent(spade.agent.Agent):
    """Temporary UI agent that requests parcel allocation."""

    def __init__(self, jid, password, parcel):
        super().__init__(jid, password)

        self.parcel = parcel
        self.result = None
        self.error = None

    class RequestBehaviour(OneShotBehaviour):

        async def run(self):
            agent = self.agent
            parcel_id = str(agent.parcel["parcel_id"])

            request = Message(to=COORDINATOR_JID)
            request.set_metadata(
                "performative",
                "request",
            )
            request.set_metadata(
                "ontology",
                "parcel-delivery",
            )
            request.set_metadata(
                "message_type",
                "allocation-request",
            )
            request.body = json.dumps(agent.parcel)

            try:
                # Send from the SPADE behaviour.
                await self.send(request)

                print(
                    f"[UI] Allocation request sent for {parcel_id}"
                )

                deadline = (
                    asyncio.get_running_loop().time()
                    + RESPONSE_TIMEOUT_SECONDS
                )

                while True:
                    remaining = (
                        deadline
                        - asyncio.get_running_loop().time()
                    )

                    if remaining <= 0:
                        agent.error = (
                            "Timed out waiting for the Coordinator. "
                            "The request may still have been processed. "
                            "Check allocation history before retrying."
                        )
                        return

                    response = await self.receive(
                        timeout=min(5, remaining)
                    )

                    if response is None:
                        continue

                    sender = (
                        str(response.sender).split("/")[0].lower()
                        if response.sender
                        else ""
                    )

                    if sender != COORDINATOR_JID.lower():
                        continue

                    if (
                        response.get_metadata("ontology")
                        != "parcel-delivery"
                        or response.get_metadata("performative")
                        != "inform"
                    ):
                        continue

                    try:
                        candidate = json.loads(response.body)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if not isinstance(candidate, dict):
                        continue

                    if (
                        str(candidate.get("parcel_id"))
                        != parcel_id
                    ):
                        continue

                    agent.result = candidate
                    print(
                        f"[UI] Coordinator response received "
                        f"for {parcel_id}: "
                        f"{candidate.get('status', 'UNKNOWN')}"
                    )
                    return

            except Exception as error:
                agent.error = (
                    f"{type(error).__name__}: {error}"
                )
                print(f"[UI ERROR] {agent.error}")

    async def setup(self):
        self.add_behaviour(self.RequestBehaviour())


async def send_allocation_request(parcel):
    """
    Send a parcel allocation request to the running Coordinator.

    The XMPP server and Coordinator must already be running.
    The parcel must already be saved in SQLite.
    """
    unique_name = f"ui-{uuid.uuid4().hex[:12]}"

    agent = AllocationRequestAgent(
        f"{unique_name}@localhost",
        XMPP_PASSWORD,
        parcel,
    )

    try:
        await agent.start(auto_register=True)

        deadline = (
            asyncio.get_running_loop().time()
            + RESPONSE_TIMEOUT_SECONDS
            + 5
        )

        while (
            agent.result is None
            and agent.error is None
            and asyncio.get_running_loop().time() < deadline
        ):
            await asyncio.sleep(0.2)

        if agent.error:
            return {
                "success": False,
                "error": agent.error,
                "result": agent.result,
            }

        if agent.result is None:
            return {
                "success": False,
                "error": (
                    "No matching response received from the Coordinator. "
                    "Check the XMPP server, Coordinator, and database. "
                    "The request may already have been processed."
                ),
                "result": None,
            }

        return {
            "success": True,
            "error": None,
            "result": agent.result,
        }

    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        print(f"[UI ERROR] {message}")

        return {
            "success": False,
            "error": message,
            "result": agent.result,
        }

    finally:
        if agent.is_alive():
            await agent.stop()
