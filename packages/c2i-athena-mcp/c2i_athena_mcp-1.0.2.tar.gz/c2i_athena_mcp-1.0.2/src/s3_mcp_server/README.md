# AWS S3 MCP Server

A Model Context Protocol (MCP) server for AWS S3, exposing common S3 operations (ls, cp, mv, rm, sync, mb, rb) as MCP tools and resources.

## Structure
- s3_mcp_server/server.py: MCP server entrypoint
- s3_mcp_server/s3_client.py: S3 client wrapper (boto3 or subprocess)

## Usage

### Running the Server via VS Github Copilot

Add the following configuration to your `.vscode/mcp.json`:

```jsonc
"s3-mcp-server": {
    "command": "uvx",
    "args": [
        "--from",
        "git+https://C2i-Genomics@dev.azure.com/C2i-Genomics/RnD%20Platform/_git/c2i_alg_mcp",
        "s3-mcp",
        "--prefix-read", "s3://your-read-prefix/",
        "--prefix-write", "s3://your-write-prefix/"
    ],
    "envFile": "${workspaceFolder}/s3.env"
}
```

- Replace `s3://your-read-prefix/` and `s3://your-write-prefix/` with your desired S3 prefixes (optional).
- The `--prefix-read` and `--prefix-write` arguments restrict read and write operations to the specified S3 prefixes for security.

### Using GitHub Copilot

You can use GitHub Copilot in this project to:
- Get code suggestions for new MCP tools or S3 operations
- Refactor or extend the server and client logic
- Generate documentation and usage examples

To use Copilot, simply start typing in your editor and accept suggestions, or ask Copilot for help with specific code blocks or documentation.
