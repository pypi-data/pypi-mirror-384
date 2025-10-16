import asyncio
import os
import dotenv
from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

env_file = '/home/ec2-user/code/athena.env'
# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="uv",
    args=["--directory", "/home/ec2-user/code/c2i_alg_mcp", "run", "athena"],
    env=dotenv.dotenv_values(env_file),
)

async def main():
    # Step 2: Create MCP Client
    athena_mcp_client = await MCPStdio.create(server_params=server_params)

    try:
        # Step 3: Define an action group
        athena_action_group = ActionGroup(
            name="AthenaActionGroup",
            description="Genomic analysis using genomic data stored on AWS Athena",
            mcp_clients=[athena_mcp_client],
        )

        # Step 4: Invoke agent
        await InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly assistant that is responsible for resolving user queries on genomic data stored on AWS Athena. """,
            # Step 4.3: Provide the agent name and action group
            agent_name="athena_agent",
            action_groups=[athena_action_group],
        ).invoke(
            input_text="List your tables?"
        )

    finally:

        await athena_mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
