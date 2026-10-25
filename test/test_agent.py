import asyncio
import spade


class TestAgent(spade.agent.Agent):
    async def setup(self):
        print(f"{self.jid} started successfully!")


async def main():
    agent = TestAgent(
        "testagent@localhost",
        "TestPassword123!"
    )

    try:
        print("Starting SPADE agent...")
        await agent.start(auto_register=True)
        print("Agent is running.")
        await asyncio.sleep(3)
    except Exception as error:
        print(f"Agent startup failed: {type(error).__name__}: {error}")
    finally:
        await agent.stop()
        print("Agent stopped.")


if __name__ == "__main__":
    asyncio.run(main())