# AWS Athena MCP Server

A Model Context Protocol (MCP) server for interacting with AWS Athena via natural language.

## Features

- List databases and tables in AWS Athena
- Get table schemas
- Execute SQL queries and retrieve results
- Track query history and execution status
- Cancel running queries

## Installation

### Using UV (recommended)

```bash
uv install git+https://github.com/yourusername/athena_mcp_server.git
```

Or install from the local directory:

```bash
# Clone the repository
git clone https://github.com/yourusername/athena_mcp_server.git
cd athena_mcp_server

# Install with UV
uv install .
```

### Using pip

```bash
pip install git+https://github.com/yourusername/athena_mcp_server.git
```

## Configuration

Create a `config.json` file with your AWS credentials:

```json
{
    "region_name": "us-east-1",
    "s3_output_location": "s3://your-athena-results-bucket/path/",
    "profile_name": "your-aws-profile"
}
```

Alternatively, you can use AWS environment variables:
- `AWS_REGION`
- `S3_OUTPUT_LOCATION`
- `AWS_PROFILE`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Usage

### Command Line

Run the server with your configuration:

```bash
# Using a config file
athena-mcp --config /path/to/config.json

# Using direct parameters
athena-mcp --region us-east-1 --s3-output s3://your-bucket/path/ --profile your-profile

# Run in development mode with the MCP Inspector UI
athena-mcp --config /path/to/config.json --dev
```

### Claude Desktop Integration

To use with Claude Desktop:

1. Install the MCP server:
```bash
mcp install athena_mcp_server --name "AWS Athena"
```

2. Configure AWS credentials:
```bash
mcp install athena_mcp_server -v AWS_REGION=us-east-1 -v S3_OUTPUT_LOCATION=s3://your-bucket/path/ -v AWS_PROFILE=your-profile
```

### Programmatic Usage

```python
from athena_mcp_server.server import mcp

config = {
    "region_name": "us-east-1",
    "s3_output_location": "s3://your-athena-results-bucket/path/",
    "profile_name": "your-aws-profile"
}

# Run the server
mcp.run(config=config)
```

## API Reference

### Resources

- `databases://` - List all available databases
- `tables://{database}` - List tables in a specific database
- `schema://{database}/{table}` - Get schema for a specific table
- `results://{execution_id}` - Get results for a completed query
- `history://` - Get history of executed queries

### Tools

- `list_databases()` - List all available databases
- `list_tables(database: str)` - List tables in a database
- `describe_table(database: str, table: str)` - Get table schema
- `execute_query(query: str, database: str = None, wait_for_completion: bool = True)` - Execute an SQL query
- `get_query_status(execution_id: str)` - Check the status of a query
- `get_results(execution_id: str, max_results: int = 1000)` - Get query results
- `cancel_query(execution_id: str)` - Cancel a running query

### Prompts

- `list_databases_prompt()` - Guide for listing databases
- `query_syntax_guide()` - Guide for writing SQL queries for AWS Athena

## Example Conversations

### Exploring Databases and Tables

```
User: What databases are available in AWS Athena?
AI: I'll check the available databases for you.

[Uses list_databases tool]
Available databases:
- analytics_db
- sales_data
- user_events
- marketing_data

User: Show me the tables in the analytics_db database
AI: Here are the tables in the analytics_db database:

[Uses list_tables tool with database="analytics_db"]
Tables in database 'analytics_db':
- user_sessions
- page_views
- conversion_events
- ad_impressions
```

### Executing Queries

```
User: Get me the top 5 products by sales from the sales_data.products table
AI: I'll query the top 5 products by sales for you.

[Uses execute_query tool]
Query executed successfully with ID: 12345-abcde-67890

| product_id | product_name | total_sales |
| ---------- | ------------ | ----------- |
| P123       | Laptop       | 256789.99   |
| P456       | Smartphone   | 198654.50   |
| P789       | Headphones   | 87654.25    |
| P234       | Tablet       | 76543.75    |
| P567       | Monitor      | 65432.25    |

5 rows returned
```

## License

MIT