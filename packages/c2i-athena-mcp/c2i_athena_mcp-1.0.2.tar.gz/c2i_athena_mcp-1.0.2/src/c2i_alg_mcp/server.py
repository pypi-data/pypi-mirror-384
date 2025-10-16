import asyncio
import io
import subprocess
import re
from contextlib import redirect_stdout, redirect_stderr
import traceback
import logging
import os
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import pandas as pd
from sqlalchemy import create_engine, inspect, text
import boto3

# Configure logging at module level
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.getenv('LOG_DIR', None)
    if not log_dir:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'athena_mcp_server.log')
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler for immediate visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # File handler for persistent logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    return logger

# Initialize logging
logger = setup_logging()
logger.info("Athena MCP Server starting up")

region = 'eu-west-1'
athena_url = f"athena.{region}.amazonaws.com"
athena_port = '443' #Update, if port is different
athena_db = 'raw_main' #from user defined params
glue_databucket_name ='c2i-data-lake-1-eu-west-1/athena/'
s3stagingathena = f's3://airflow-research-integration-1-eu-west-1/athena_query_results/'
athena_wkgrp = 'primary'
athena_connection_string = f"awsathena+rest://@{athena_url}:{athena_port}/{athena_db}?s3_staging_dir={s3stagingathena}/&work_group={athena_wkgrp}"


class AthenaMCPServer:
    def __init__(self):
        self.server = Server("athena")
        
        athena_engine = create_engine(
            athena_connection_string, 
            connect_args={"region_name": region}, 
            echo=True
        )
        self.engine = athena_engine
        
        # Use the module logger
        self.logger = logger

        # Set up handlers using decorators
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return await self.handle_list_tools()
            
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            return await self.handle_call_tool(name, arguments)

    async def handle_list_tools(self) -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
            name="list_tables",
            description="Retrieve a list of all tables available in the current Athena database.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
            ),
            types.Tool(
            name="athena_query",
            description="Run a SQL query against the Athena database and retrieve the results.",
            inputSchema={
                "type": "object",
                "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query to execute on the Athena database.",
                },
                },
                "required": ["sql_query"],
            },
            ),
            types.Tool(
            name="list_columns",
            description="Retrieve the column names and details of a specified table in the Athena database.",
            inputSchema={
                "type": "object",
                "properties": {
                "table_name": {
                    "type": "string",
                    "description": "The name of the table to retrieve column details for.",
                },
                },
                "required": ["table_name"],
            },
            ),
            types.Tool(
            name="list_executions",
            description="Retrieve a list of recent query executions in Athena, including query and output locations.",
            inputSchema={
                "type": "object",
                "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "The maximum number of query executions to retrieve.",
                },
                },
                "required": ["max_results"],
            },
            ),
        ]

    async def handle_call_tool(
        self, name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""

        self.logger.info(f"Tool call: {name}")
        self.logger.info(f"Arguments: {arguments}")
        
        try:
            result = getattr(self, name)(**(arguments or {}))
            
            # Log successful execution
            self.logger.info(f"Tool {name} executed successfully")
            
            return [
                types.TextContent(
                    type="text",
                    text=result
                )
            ]
                
        except Exception as e:  # noqa: F841
            # Capture and format any exceptions
            error_msg = f"Error executing code:\n{traceback.format_exc()}"
            
            # Log the error
            self.logger.error(f"Tool {name} failed: {str(e)}")
            self.logger.debug(f"Error details: {error_msg}")
            
            return [
                types.TextContent(
                    type="text",
                    text=error_msg
                )
            ]
        
    def list_tables(self) -> str:
        """
        List all tables in the current Athena database.
        """
        try:
            db = self.engine
            inspector = inspect(db)
            table_names = inspector.get_table_names()
            if not table_names or len(table_names)==0:
                return "No tables found in the current Athena database."
            return f"Tables in the current Athena database: {', '.join(table_names)}"
        except Exception as e:
            return f"Error listing tables: {str(e)}"

    def athena_query(self, sql_query: str) -> str:
        """
        Execute a SQL query against the Athena database.
        """
        try:
            db = self.engine
            with db.connect() as connection:
                query = connection.execute(text(sql_query))
                columns = query.keys()
                rows = query.fetchall()
            if not rows:
                return "No results found."
            
            # Format the results as a string
            formatted_result = pd.DataFrame(rows, columns=columns).to_string()
            return f"Query Result:\n{formatted_result}"
        except Exception as e:
            return f"Error executing query: {str(e)}"

    def list_columns(self, table_name: str) -> str:
        """
        List the columns of a specified table in the Athena database.
        """
        try:
            db = self.engine
            inspector = inspect(db)
            columns = inspector.get_columns(table_name)
            if not columns:
                return f"No columns found for table '{table_name}'."
            
            column_names = [col['name'] for col in columns]
            return f"Columns in table '{table_name}': {', '.join(column_names)}"
        except Exception as e:
            return f"Error listing columns for table '{table_name}': {str(e)}"
    
    def list_executions(self, max_results) -> str:
        # Initialize the Athena client
        athena_client = boto3.client('athena', region_name=region) # Ensure you specify the correct region

        # Retrieve the list of query execution IDs (adjust MaxResults as needed)
        query_execution_ids = athena_client.list_query_executions(MaxResults=max_results, WorkGroup=athena_wkgrp)['QueryExecutionIds']

        responses = []
        # Fetch details for each query execution
        for qid in query_execution_ids:
            response = athena_client.get_query_execution(QueryExecutionId=qid)
            query_execution = response['QueryExecution']
            
            # Extract the query statement
            query = query_execution['Query']
            
            # Extract the output location URI
            output_location = query_execution['ResultConfiguration']['OutputLocation']
            
            responses.append({'query':query,'output':output_location})
        return pd.DataFrame(responses).to_string()
        
    async def run(self):
        """Run the server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="python-repl",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    server = AthenaMCPServer()
    await server.run()

if __name__ == "__main__":
    server = AthenaMCPServer()
    print(server.list_tables())
    # asyncio.run(main())
