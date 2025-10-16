# AWS Step Functions MCP Server

A Model Context Protocol (MCP) server for AWS Step Functions that allows language models to interact with and manage AWS Step Functions resources through a structured API.

## Overview

This MCP server provides a comprehensive interface for managing AWS Step Functions state machines and executions. It enables language models to:

- List and explore AWS Step Functions state machines
- Create new state machines with Amazon States Language definitions
- Start, monitor, and stop executions
- View execution history and results
- Update or delete state machines

## Installation

### Using UV (Recommended)

This project uses [uv](https://github.com/astral-sh/uv) for package management, a fast Python package installer and resolver.

```bash
# Clone the repository
git clone https://github.com/yourusername/stepfunctions_mcp_server.git
cd stepfunctions_mcp_server

# Install using uv
uv pip install -e .
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/stepfunctions_mcp_server.git
cd stepfunctions_mcp_server

# Install using pip
pip install -e .
```

## Configuration

1. Create an environment file (`.env`) with your AWS credentials:

```bash
AWS_REGION=us-east-1
AWS_PROFILE=default
# OR use direct credentials (not recommended for production)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
```

2. Save this file in the project directory or a location of your choice.

## Running the Server

### Command Line

Run the server directly:

```bash
# Using installed package
python -m stepfunctions_mcp_server.server

# Using UV
uv run -m stepfunctions_mcp_server.server
```

### Configuring in VS Code with MCP Extension

1. Install the [MCP Extension](https://marketplace.visualstudio.com/items?itemName=AntreasAntoniou.mcp) for VS Code.

2. Add the Step Functions MCP server to your MCP configuration:
   - Open VS Code settings (File > Preferences > Settings)
   - Navigate to Extensions > MCP
   - Click "Edit in settings.json"
   - Add the following to the `mcp.servers` section:

```json
"mcp.servers": {
    "stepfunctions-mcp-server": {
        "command": "uv",
        "args": [
            "run",
            "--directory",
            "${workspaceFolder}/stepfunctions_mcp_server",
            "-m",
            "stepfunctions_mcp_server.server"
        ],
        "envFile": "${workspaceFolder}/.env"
    }
}
```

3. Start the server from VS Code:
   - Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
   - Type "MCP: Start Server"
   - Select "stepfunctions-mcp-server"

## Available Resources

The server provides the following resource endpoints:

- `state-machines://` - List all state machines
- `state-machine://{machine_arn}` - Get details for a specific state machine
- `executions://{machine_arn}` - List executions for a state machine
- `execution://{execution_arn}` - Get details for a specific execution
- `execution-history://{execution_arn}` - Get execution event history
- `history://` - View tracked execution history

## Tools

The server provides function-based endpoints for programmatically interacting with Step Functions:

- Functions for managing state machines (create, update, delete)
- Functions for managing executions (start, stop, describe)
- Functions for querying history and status information

## Amazon States Language Guide

The server includes a helpful prompt with guidance for writing Amazon States Language definitions, accessible via the MCP interface.

## IAM Permissions

The AWS credentials used to run this MCP server should have the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "states:ListStateMachines",
                "states:DescribeStateMachine",
                "states:CreateStateMachine",
                "states:UpdateStateMachine",
                "states:DeleteStateMachine",
                "states:ListExecutions",
                "states:StartExecution",
                "states:StopExecution",
                "states:DescribeExecution",
                "states:GetExecutionHistory"
            ],
            "Resource": "*"
        }
    ]
}
```

## Security Considerations

- Store AWS credentials securely and never commit them to version control
- Consider using AWS IAM roles and policies to restrict permissions to only what is needed
- For production environments, use environment variables or AWS credential providers rather than hardcoded credentials

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
EOL