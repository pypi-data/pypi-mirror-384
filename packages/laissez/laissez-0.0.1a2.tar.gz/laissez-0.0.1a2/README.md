# Laissez

Agent spending you can trust


## Quickstart

#### Create a paid MCP app

```
from fastmcp import FastMCP
import random

from laissez.server import PaidTool, create_paid_mcp_app


mcp = FastMCP("my-example-server")

@mcp.tool
def roll_die() -> int:
    return random.randint(1,6)

paid_tools = [
    PaidTool(name="roll_die", price=0.001, description="Rolls a die")
]

if __name__ == "__main__":
    import uvicorn
    import asyncio

    app = asyncio.run(create_paid_mcp_app(mcp, paid_tools))
    uvicorn.run(app, host="127.0.0.1", port=8000)
```


#### Create a paying MCP client

```
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv

from laissez.client import LaissezClient


load_dotenv()


BASE_URL = 'dice-roll.laissez.xyz'
laissez = LaissezClient()


server = MCPServerStreamableHTTP(
    url=f'{BASE_URL}/mcp',
    http_client=laissez
)


agent = Agent(
    model='openai:gpt-5-mini',
    instructions='Show your working out',
    toolsets=[server]
)


async def main():
    result = await agent.run("Roll a dice twice then multiply the two results and return the final result")

    print(result.output)


if __name__ == '__main__':
    asyncio.run(main())
```

## Examples

The above quickstart can be found in `examples/mcp`.
Be sure to:
* Set OPENAI_API_KEY in `.env` if you are running the client
* Set WALLET_PRIVATE_KEY in `.env` or follow the Laissez wizard to create a test account
* Add faucet to your wallet by visiting https://faucet.circle.com, selecting `Base Sepolia`, and pasting your wallet address