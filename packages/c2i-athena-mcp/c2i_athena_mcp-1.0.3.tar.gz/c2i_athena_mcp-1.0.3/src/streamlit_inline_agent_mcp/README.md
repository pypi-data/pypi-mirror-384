# Bedrock InlineAgent with MCP + Streamlit UI

## Prerequisites

1. **Install 'uv'**
    ```bash
    # For Unix/macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # For Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2. **Create mcp.json file**
    - Create a configuration file with your MCP settings
    - Example format:
    ```json
    {
    "servers": {
        "s3-mcp-server": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://C2i-Genomics@dev.azure.com/C2i-Genomics/RnD%20Platform/_git/c2i_alg_mcp",
                "s3-mcp",
                "--prefix-read", "s3://your-read-prefix/",
                "--prefix-write", "s3://your-write-prefix/"
            ],
            "envFile": "/path/to/env/file"
        }
        }
    }
    ```

3. **Set up AWS permissions for Bedrock**
    - Ensure your AWS credentials have access to Bedrock services
    - Configure AWS CLI or set environment variables

## Running the App

### Option 1: With uvx + streamlit cli
```bash
uvx --from git+https://C2i-Genomics@dev.azure.com/C2i-Genomics/RnD%20Platform/_git/c2i_alg_mcp streamlit run src/streamlit_inline_agent_mcp/mcp_agent_ui.py -- --mcp-config path/to/mcp.json
```

### Option 2: With uv + streamlit cli
1. Clone the git repository
    ```bash
    git clone https://C2i-Genomics@dev.azure.com/C2i-Genomics/RnD%20Platform/_git/c2i_alg_mcp
    cd c2i_alg_mcp
    ```
2. Run the application
    ```bash
    uv run streamlit run src/streamlit_inline_agent_mcp/mcp_agent_ui.py -- --mcp-config path/to/mcp.json
    ```

### Option 3: With uvx + python
```bash
uvx --from git+https://C2i-Genomics@dev.azure.com/C2i-Genomics/RnD%20Platform/_git/c2i_alg_mcp python src/streamlit_inline_agent_mcp/launch.py -- --mcp-config path/to/mcp.json
```