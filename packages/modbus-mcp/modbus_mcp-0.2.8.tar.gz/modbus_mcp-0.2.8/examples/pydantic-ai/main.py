import asyncio

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP


async def main():
    mcp = MCPServerStreamableHTTP("http://127.0.0.1:8000/mcp/")

    agent = Agent(
        "openai:gpt-4o",
        mcp_servers=[mcp],
        system_prompt=(
            "You are a Modbus expert. Use the available tools to interact with "
            "Modbus devices via the MCP server."
        ),
    )

    async with agent.run_mcp_servers():
        for prompt in [
            "Read the content of 40010 on 127.0.0.1:502.",
            "Write [123, 45, 678] to registers starting at 40011.",
        ]:
            resp = await agent.run(prompt)
            print(resp.output)


if __name__ == "__main__":
    asyncio.run(main())
