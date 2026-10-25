
import asyncio
import os
import sys

from agents.coordinator_agent import CoordinatorAgent
from agents.hub_agent import ParcelHubAgent
from agents.courier_agent import CourierAgent
from services.database import (
    initialize_database,
    get_all_couriers,
)


XMPP_PASSWORD = os.getenv(
    "MAS_AGENT_XMPP_PASSWORD",
    "TestPassword123!",
)

COORDINATOR_JID = "coordinator@localhost"
HUB_JID = "hub@localhost"

# Used only when the database has no registered couriers.
DEFAULT_COURIER = {
    "courier_id": "C001",
    "jid": "courier1@localhost",
    "delivery_locations": ["Colombo", "Kandy"],
    "capacity_kg": 10.0,
}


async def start_agent(agent, label):
    """Start an SPADE agent and report its startup status."""
    print(f"[MAIN] Starting {label}...")

    await agent.start(auto_register=True)

    print(f"[MAIN] {label} started successfully.")
    return agent


async def main():
    agents = []

    try:
        # Initialize the existing project database.
        initialize_database()

        print("=" * 55)
        print(" CollaborativeDeliveryMAS - Agent Launcher")
        print("=" * 55)

        # Start the Coordinator first.
        coordinator = CoordinatorAgent(
            COORDINATOR_JID,
            XMPP_PASSWORD,
        )
        await start_agent(coordinator, "Coordinator")
        agents.append(coordinator)

        # Start the Parcel Hub.
        hub = ParcelHubAgent(
            HUB_JID,
            XMPP_PASSWORD,
        )
        await start_agent(hub, "Parcel Hub")
        agents.append(hub)

        # Read the saved courier configurations.
        couriers = get_all_couriers()

        # Provide a default courier for a fresh database.
        # This does not delete or restore any existing records.
        if not couriers:
            print(
                "[MAIN] No couriers are registered. "
                "Starting the default courier C001."
            )
            couriers = [DEFAULT_COURIER]

        # Start each registered Courier agent.
        for courier_record in couriers:
            courier_id = courier_record["courier_id"]

            jid = courier_record.get("jid")
            if not jid:
                jid = f"{courier_id.lower()}@localhost"

            courier_agent = CourierAgent(
                jid=jid,
                password=XMPP_PASSWORD,
                courier_id=courier_id,
                delivery_locations=courier_record[
                    "delivery_locations"
                ],
                capacity_kg=courier_record["capacity_kg"],
            )

            await start_agent(
                courier_agent,
                f"Courier {courier_id}",
            )
            agents.append(courier_agent)

        print("\n[MAIN] All configured agents have started.")
        print("[MAIN] Press Ctrl+C to stop the agents.")

        # Keep the launcher running while agents operate.
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[MAIN] Shutdown requested.")

    except Exception as error:
        print(
            f"\n[MAIN ERROR] {type(error).__name__}: {error}"
        )
        raise

    finally:
        # Stop agents in reverse startup order.
        for agent in reversed(agents):
            try:
                if agent.is_alive():
                    print(f"[MAIN] Stopping {agent.jid}...")
                    await agent.stop()
            except Exception as error:
                print(
                    f"[MAIN WARNING] Could not stop "
                    f"{agent.jid}: {error}"
                )

        print("[MAIN] Agent shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
