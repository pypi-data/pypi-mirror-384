import os
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# Import the MCP server library
from mcp.server.fastmcp import FastMCP, Context

# Import the Athena client
from athena_mcp_server.athena_client import AthenaClient

# Import MRD calculation tools
from athena_mcp_server.mrd_calculation_tools import MRDCalculator

# Import file utilities
from .helpers.prompts import read_instruction_file
from .helpers.files import save_data_to_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dictionary to store query execution IDs for tracking
query_executions = {}

# Environment variable names
AWS_S3_OUTPUT_URI = "AWS_S3_OUTPUT_URI"

def format_schema(database, table, schema):
    formatted_output = (
    f"Schema for table '{table}' in database '{database}':\n\n"
    "| Column Name | Data Type | Partition |\n"
    "| ----------- | --------- |-----------|\n")

    for column in schema:
        formatted_output += f"| {column['name']} | {column['type']} | {column.get('is_partition', False)} |\n"

    return formatted_output

@dataclass
class AppContext:
    athena_client: AthenaClient
    mrd_calculator: MRDCalculator

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup using environment variables    
    s3_output_location = os.environ.get(AWS_S3_OUTPUT_URI)
    
    logger.info(f"Using S3 output location: {s3_output_location}")
    
    athena_client = AthenaClient(
        s3_output_location=s3_output_location
    )
    
    # Initialize MRD calculator
    mrd_calculator = MRDCalculator(athena_client)
    
    try:
        yield AppContext(athena_client=athena_client, mrd_calculator=mrd_calculator)
    finally:
        # Cleanup on shutdown
        # Any cleanup code if needed
        pass

# Create the MCP Server with lifespan
mcp = FastMCP("AWS Athena", 
              dependencies=["boto3", "pandas", "pillow", "numpy", "mcp>=0.1.0"],
              lifespan=app_lifespan)

# Resource endpoints
@mcp.resource("databases://databases")
async def get_databases() -> str:
    """List all available databases in AWS Athena"""
    # Access context through the request's state
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    athena_client = state.lifespan_context.athena_client
    
    databases = athena_client.list_databases()
    formatted_output = "Available databases:\n\n"
    for db in databases:
        formatted_output += f"- {db}\n"
    return formatted_output


@mcp.resource("tables://{database}")
async def get_tables(database: str) -> str:
    """List all tables in the specified database"""
    # Access context through the request's state
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    athena_client = state.lifespan_context.athena_client
    
    tables = athena_client.list_tables(database)
    formatted_output = f"Tables in database '{database}':\n\n"
    for table in tables:
        formatted_output += f"- {table}\n"
    return formatted_output


@mcp.resource("schema://{database}/{table}")
async def get_table_schema(database: str, table: str) -> str:
    """Get the schema of a table"""
    # Access context through the request's state
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    athena_client = state.lifespan_context.athena_client
    
    schema = athena_client.get_table_schema(database, table)
    
    formatted_output = format_schema(database, table, schema)
        
    return formatted_output


@mcp.resource("results://{execution_id}")
async def get_query_results(execution_id: str) -> str:
    """Get results for a completed query"""
    # Access context through the request's state
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    athena_client = state.lifespan_context.athena_client
    
    results = athena_client.get_query_results(execution_id)
    
    if results["status"] != "SUCCEEDED":
        error_reason = results.get("error_reason", "Unknown error")
        return f"Query execution {execution_id} failed: {error_reason}"
    
    formatted_output = f"Results for query execution {execution_id}:\n\n"
    formatted_output += _format_results_as_table(results)
    return formatted_output


@mcp.resource("history://history")
async def get_query_history() -> str:
    """Get history of executed queries"""
    if not query_executions:
        return "No query history available"
        
    formatted_output = "Recent query executions:\n\n"
    
    for exec_id, details in sorted(
        query_executions.items(), 
        key=lambda x: x[1].get('timestamp', ''), 
        reverse=True
    )[:10]:
        formatted_output += f"ID: {exec_id}\n"
        formatted_output += f"Status: {details.get('status', 'Unknown')}\n"
        formatted_output += f"Time: {details.get('timestamp', 'Unknown')}\n"
        query_preview = details.get('query', '')[:50] + "..." if len(details.get('query', '')) > 50 else details.get('query', '')
        formatted_output += f"Query: {query_preview}\n\n"
        
    return formatted_output


# Tool endpoints
@mcp.tool()
def list_databases(ctx: Context) -> List[str]:
    """List all available databases in AWS Athena"""
    athena_client = ctx.request_context.lifespan_context.athena_client
    databaes_list = athena_client.list_databases()
    if len(databaes_list)==0:
        return 'none'
    return ','.join(athena_client.list_databases())


@mcp.tool()
def list_tables(ctx: Context, database: str) -> List[str]:
    """List all tables in a database"""
    athena_client = ctx.request_context.lifespan_context.athena_client
    tables_list = athena_client.list_tables(database)
    if len(tables_list)==0:
        return 'none'
    return  ','.join(athena_client.list_tables(database))


@mcp.tool()
def describe_table(ctx: Context, database: str, table: str) -> List[Dict[str, str]]:
    """Get the schema of a table"""
    athena_client = ctx.request_context.lifespan_context.athena_client
    schema = athena_client.get_table_schema(database, table)
    formatted_output = format_schema(database, table, schema)
    return formatted_output

@mcp.tool()
def get_schema_overview(ctx: Context) -> List[str]:
    """
    Get comprehensive overview of all database schemas and table structures.
    
    Use this tool before building queries to understand available tables, columns, data types,
    and partition information across all databases. More efficient than multiple list/describe calls.
    
    **IMPORTANT**: Excludes raw_main and other non-analytics databases for focus on processed data.
    """
    athena_client = ctx.request_context.lifespan_context.athena_client
    
    # Databases to exclude from schema overview (raw/unprocessed data)
    excluded_databases = ['raw_main', 'curated_main', 'integration']
    
    # Get all databases
    all_databases = athena_client.list_databases()
    databases = [db for db in all_databases if db not in excluded_databases]
    
    all_schemas = []
    
    # Add exclusion notice
    if excluded_databases:
        excluded_list = ', '.join(excluded_databases)
        all_schemas.append(f"NOTE: Excluded databases for analytics focus: {excluded_list}")
        all_schemas.append("Focus on 'main' (processed data) and 'external' (reference data)\n")
    
    for database in databases:
        ctx.info(f"Processing database: {database}")
        
        try:
            # Get all tables in this database
            tables = athena_client.list_tables(database)
            
            if not tables:
                all_schemas.append(f"Database '{database}': No tables found\n")
                continue
                
            # Add database header
            all_schemas.append(f"\n{'='*60}")
            all_schemas.append(f"DATABASE: {database.upper()}")
            all_schemas.append(f"{'='*60}")
            all_schemas.append(f"Tables found: {len(tables)}")
            all_schemas.append(f"{'='*60}\n")
            
            # Get schema for each table
            for table in tables:
                try:
                    schema = athena_client.get_table_schema(database, table)
                    formatted_schema = format_schema(database, table, schema)
                    all_schemas.append(formatted_schema)
                    all_schemas.append("\n" + "-"*50 + "\n")
                except Exception as e:
                    all_schemas.append(f"Error getting schema for table '{table}' in database '{database}': {str(e)}\n")
                    
        except Exception as e:
            all_schemas.append(f"Error processing database '{database}': {str(e)}\n")
    
    return all_schemas


@mcp.tool()
def execute_query(ctx: Context, query: str, database: str = None, wait_for_completion: bool = True) -> Dict[str, Any]:
    """
    Execute an SQL query on AWS Athena
    
    Args:
        query: SQL query to execute
        database: Database to query (optional)
        wait_for_completion: Whether to wait for query completion
        
    Returns:
        Query execution result information as dict containing:
        - execution_id: Query execution ID (use with save_results_to_csv)
        - status: "SUCCEEDED", "FAILED", or "SUBMITTED" 
        - result_table: Formatted markdown table (if successful and wait_for_completion=True)
        - columns: Column names array
        - rows: Result data rows  
        - row_count: Number of rows returned
        - runtime_seconds: Query execution time
        - data_scanned_mb: Amount of data processed (impacts cost)
        
    Related Tools:
        - Follow with: save_results_to_csv
    """
    global query_executions
    athena_client = ctx.request_context.lifespan_context.athena_client
    
    # Execute the query
    if wait_for_completion:
        ctx.info(f"Running query on {database or 'default'} database...")
        result = athena_client.execute_query(query, database, wait=True)
        
        # Store in tracking dictionary
        execution_id = result["execution_id"]
        status = result["status"]
        query_executions[execution_id] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "query": query
        }
        
        if status == "SUCCEEDED":
            # Use the new unified method to get comprehensive results
            summary = athena_client.get_query_results_with_summary(execution_id)
            
            # Add formatted table output for display
            table_output = _format_results_as_table(summary)
            ctx.info(f"Query executed successfully with ID: {execution_id} (Runtime: {summary.get('runtime_seconds', 0)}s, Data scanned: {summary.get('data_scanned_mb', 0)}MB)")
            
            return {
                "execution_id": execution_id,
                "status": "SUCCEEDED",
                "message": f"Query executed successfully with ID: {execution_id}",
                "result_table": table_output,
                "columns": summary.get("columns", []),
                "rows": summary.get("rows", []),
                "row_count": summary.get("row_count", 0),
                "runtime_seconds": summary.get("runtime_seconds", 0),
                "data_scanned_mb": summary.get("data_scanned_mb", 0),
                "data_scanned_bytes": summary.get("data_scanned_bytes", 0)
            }
        else:
            error_reason = result.get("error_reason", "Unknown error")
            ctx.warning(f"Query execution failed: {error_reason}")
            return {
                "execution_id": execution_id,
                "status": status,
                "message": f"Query execution failed: {error_reason}",
                "error_reason": error_reason
            }
    else:
        # Submit the query without waiting
        result = athena_client.execute_query(query, database, wait=False)
        execution_id = result["execution_id"]
        
        # Store in tracking dictionary
        query_executions[execution_id] = {
            "status": "RUNNING",
            "timestamp": datetime.now().isoformat(),
            "query": query
        }
        
        ctx.info(f"Query submitted with execution ID: {execution_id}")
        return {
            "execution_id": execution_id,
            "status": "SUBMITTED",
            "message": f"Query submitted with execution ID: {execution_id}"
        }


@mcp.tool()
def get_query_status(ctx: Context, execution_id: str) -> Dict[str, Any]:
    """
    Get the status of a query execution
    
    Args:
        execution_id: Query execution ID
        
    Returns:
        Query status information
    """
    athena_client = ctx.request_context.lifespan_context.athena_client
    query_details = athena_client.athena_client.get_query_execution(
        QueryExecutionId=execution_id
    )
    
    state = query_details['QueryExecution']['Status']['State']
    
    # Update status in our tracking dictionary
    if execution_id in query_executions:
        query_executions[execution_id]["status"] = state
    
    if state == "SUCCEEDED":
        return {
            "execution_id": execution_id,
            "status": state,
            "message": "Query completed successfully"
        }
    elif state in ["FAILED", "CANCELLED"]:
        reason = query_details['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
        return {
            "execution_id": execution_id,
            "status": state,
            "message": f"Query {state.lower()}: {reason}",
            "error_reason": reason
        }
    else:
        return {
            "execution_id": execution_id,
            "status": state,
            "message": f"Query status: {state}"
        }


@mcp.tool()
def save_results_to_csv(ctx: Context, execution_id: str, max_results: int = None) -> str:
    """
    Save results of a completed Athena query to a CSV file in the 'outputs' directory.
    
    This tool saves query results from any completed Athena execution to a structured CSV file
    with timestamps for easy tracking and analysis.
    
    File Location: ./outputs/ directory (created automatically if it doesn't exist)
    Filename Format: athena_results_YYYYMMDD_HHMMSS_{execution_id}.csv
    
    Usage Examples:
    - Save sample listing: save_results_to_csv(execution_id="abc123")  
    - Save with limit: save_results_to_csv(execution_id="abc123", max_results=500)
    
    Args:
        execution_id: Query execution ID
        max_results: Maximum number of results to retrieve
    Returns:
        Path to the saved CSV file or error message if failed
        
    Related Tools:
        - Use after: execute_query
    """
    athena_client = ctx.request_context.lifespan_context.athena_client
    
    # Use the new unified method to get results
    summary = athena_client.get_query_results_with_summary(execution_id, max_results)
    
    if summary["status"] != "SUCCEEDED":
        error_reason = summary.get("error_reason", "Unknown error")
        ctx.warning(f"Unable to get results: {error_reason}")
        return f"Unable to get results: {error_reason}"
        
    columns = summary.get("columns", [])
    rows = summary.get("rows", [])
    if not columns or not rows:
        return "No results found."
    
    # Set output directory to match save_data_to_csv behavior
    output_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    df = pd.DataFrame(rows, columns=columns)
    
    # Create better filename with timestamp and execution_id at the end
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"athena_results_{timestamp}_{execution_id}.csv"
    file_path = os.path.join(output_dir, file_name)
    
    df.to_csv(file_path, index=False)
    ctx.info(f"Results saved to {file_path}")
    return file_path


@mcp.tool()
def get_results(ctx: Context, execution_id: str, max_results: int = None) -> Dict[str, Any]:
    """
    Get results of a completed query
    
    Args:
        execution_id: Query execution ID
        max_results: Maximum number of results to retrieve
        
    Returns:
        Query results
    """
    athena_client = ctx.request_context.lifespan_context.athena_client
    
    # Use the new unified method to get all result information
    summary = athena_client.get_query_results_with_summary(execution_id, max_results)
    
    if summary["status"] == "SUCCEEDED":
        # Add formatted table output for display
        table_output = _format_results_as_table(summary)
        summary["result_table"] = table_output
        
    return summary


@mcp.tool()
def cancel_query(ctx: Context, execution_id: str) -> Dict[str, Any]:
    """
    Cancel a running query
    
    Args:
        execution_id: Query execution ID
        
    Returns:
        Cancellation result
    """
    athena_client = ctx.request_context.lifespan_context.athena_client
    try:
        athena_client.athena_client.stop_query_execution(
            QueryExecutionId=execution_id
        )
        
        # Update status in our tracking dictionary
        if execution_id in query_executions:
            query_executions[execution_id]["status"] = "CANCELLED"
        
        return {
            "execution_id": execution_id,
            "status": "CANCELLED",
            "message": f"Query execution {execution_id} cancelled"
        }
    except Exception as e:
        return {
            "execution_id": execution_id,
            "status": "ERROR",
            "message": f"Error cancelling query: {str(e)}",
            "error_reason": str(e)
        }


@mcp.prompt()
def query_syntax_guide() -> str:
    """Guide for writing SQL queries for AWS Athena"""
    return """# AWS Athena SQL Query Guide

AWS Athena supports standard ANSI SQL with some specific syntax features:

## Basic Query Structure
```sql
SELECT column1, column2
FROM database_name.table_name
WHERE condition
GROUP BY column1
ORDER BY column1 DESC
LIMIT 10;
```

## Common Query Patterns

### Select all columns:
```sql
SELECT * FROM database_name.table_name LIMIT 10;
```

### Count rows:
```sql
SELECT COUNT(*) AS row_count FROM database_name.table_name;
```

### Group by with aggregation:
```sql
SELECT category, COUNT(*) AS count, AVG(amount) AS avg_amount
FROM database_name.table_name
GROUP BY category
ORDER BY count DESC;
```

### Filtering with date:
```sql
SELECT *
FROM database_name.table_name
WHERE date_column >= DATE '2023-01-01'
  AND date_column < DATE '2023-02-01';
```

### Using WITH clause for temporary tables:
```sql
WITH temp_data AS (
  SELECT user_id, SUM(amount) AS total_spent
  FROM database_name.transactions
  GROUP BY user_id
)
SELECT u.name, t.total_spent
FROM database_name.users u
JOIN temp_data t ON u.id = t.user_id
ORDER BY t.total_spent DESC;
```

### Quote column names that have special characters with double quotes
### Use partition filters to optimize queries on partitioned tables
### Target specific `rp-file-id` for precise queries when available
### When given a few filters use `AND` to combine them, unless explicitly stated otherwise
### Remember that Athena is case-sensitive for table and database names."""

# Helper function for formatting results
def _format_results_as_table(results: Dict[str, Any]) -> str:
    """Format query results as a markdown table."""
    columns = results.get("columns", [])
    rows = results.get("rows", [])
    
    if not columns or not rows:
        return "No results found."
        
    # Create table header
    table = "| " + " | ".join(columns) + " |\n"
    table += "| " + " | ".join(["---" for _ in columns]) + " |\n"
    
    # Add rows
    for row in rows:
        formatted_row = []
        for cell in row:
            if cell is None:
                formatted_row.append("NULL")
            else:
                formatted_row.append(str(cell))
        table += "| " + " | ".join(formatted_row) + " |\n"
        
    # Add summary
    table += f"\n{len(rows)} rows returned"
    
    return table

# MRD (Minimal Residual Disease) Calculation Tools Version 2
@mcp.tool()
def calculate_mrd_score_for_sample(ctx: Context,
                                     dataset: str,
                                     run_name: Optional[str] = None,
                                     algo_version: Optional[str] = None,
                                     subject: Optional[str] = None,
                                     sample: Optional[str] = None,
                                     database: str = "main") -> Dict[str, Any]:
    """
    This tool implements genomic filtering pipeline as specified
    in the MRD Detection Rate Calculation Instructions.
    
    AUTOMATIC CSV SAVING:
    Results are automatically saved to a CSV file in the 'outputs' directory with the filename format:
    'mrd_sample_result_{dataset}_{subject}_{sample}_{timestamp}.csv' (e.g., 'mrd_sample_result_DATASET_NAME_SUBJECT123_SAMPLE456_20250915_143022.csv')
    
    The CSV file contains the MRD calculation result with columns:
    - dataset, run_name, algo_version, subject, sample
    - sites_with_alt, total_sites, detection_rate, status
    
    Save Location: ./outputs/ directory (created automatically if it doesn't exist)
    
    Args:
        dataset: Dataset name for partitioning (e.g., "DATASET_NAME")
        run_name: Optional run name for partitioning (e.g., "RUN_NAME")
        algo_version: Optional algorithm version for partitioning (e.g., "main-YYYYMMDD")
        subject: Optional subject identifier
        sample: Optional sample identifier  
        database: Database containing the genomic data (default: main)
        
    Returns:
        Dict containing MRD analysis results:
        - dataset, run_name, algo_version, subject, sample
        - sites_with_alt: Number of sites with alternative alleles
        - total_sites: Total number of sites after filtering
        - detection_rate: MRD detection rate (0-1)
        - status: Operation status
        - csv_path: Path to the automatically saved CSV file (if successful)
    """
    mrd_calculator = ctx.request_context.lifespan_context.mrd_calculator
    
    ctx.info(f"Calculating MRD score for sample: {subject or 'all'}/{sample or 'all'}")
    
    result = mrd_calculator.calculate_mrd_score_for_sample(
        dataset=dataset,
        run_name=run_name,
        algo_version=algo_version,
        subject=subject,
        sample=sample,
        database=database
    )
    
    if result.get("status") == "success":
        detection_rate = result.get("detection_rate", 0.0)
        sites_with_alt = result.get("sites_with_alt", 0)
        total_sites = result.get("total_sites", 0)
        ctx.info(f"MRD calculation complete: Detection rate={detection_rate}, Sites with alt={sites_with_alt}, Total sites={total_sites}")
        
        # Save result to CSV file
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create descriptive filename with sample identifiers
            subject_part = f"_{subject}" if subject else "_all_subjects"
            sample_part = f"_{sample}" if sample else "_all_samples"
            filename = f"mrd_sample_result_{dataset}{subject_part}{sample_part}_{timestamp}"
            
            csv_path = save_data_to_csv(ctx, [result], filename)
            ctx.info(f"Result automatically saved to CSV: {csv_path}")
            
            # Add CSV path to the result
            result["csv_path"] = csv_path
            
        except Exception as e:
            ctx.warning(f"Failed to save result to CSV: {str(e)}")
    else:
        ctx.warning(f"MRD calculation failed: {result.get('error', 'Unknown error')}")
    
    return result

@mcp.tool()
def calculate_mrd_for_dataset(ctx: Context,
                                dataset: str,
                                run_name: Optional[str] = None,
                                algo_version: Optional[str] = None,
                                database: str = "main") -> List[Dict[str, Any]]:
    """
    This tool processes all samples in the specified dataset using genomic filtering pipeline as specified in the MRD Detection Rate Calculation Instructions.
    
    AUTOMATIC CSV SAVING:
    Results are automatically saved to a CSV file in the 'outputs' directory with the filename format:
    'mrd_dataset_results_{dataset}_{timestamp}.csv' (e.g., 'mrd_dataset_results_DATASET_NAME_20250915_143022.csv')
    
    The CSV file contains all successful MRD calculation results with columns:
    - dataset, run_name, algo_version, subject, sample
    - sites_with_alt, total_sites, detection_rate, status
    
    Save Location: ./outputs/ directory (created automatically if it doesn't exist)
    
    Args:
        dataset: Dataset name for partitioning (e.g., "DATASET_NAME") [REQUIRED]
        run_name: Optional run name for partitioning (e.g., "RUN_NAME") [OPTIONAL - defaults to None]
        algo_version: Optional algorithm version for partitioning (e.g., "main-YYYYMMDD") [OPTIONAL - defaults to None]
        database: Database containing the genomic data [OPTIONAL - defaults to "main"]
        
    Returns:
        List of dicts, each containing MRD analysis results:
        - dataset, run_name, algo_version, subject, sample
        - sites_with_alt: Number of sites with alternative alleles
        - total_sites: Total number of sites after filtering
        - detection_rate: MRD detection rate (0-1)
        - status: Operation status
    """
    mrd_calculator = ctx.request_context.lifespan_context.mrd_calculator
    
    ctx.info(f"Calculating MRD scores for dataset: {dataset}")
    ctx.info(f"Using parameters: run_name={run_name or 'all'}, algo_version={algo_version or 'all'}")
    
    results = mrd_calculator.calculate_mrd_for_dataset(
        dataset=dataset,
        run_name=run_name,
        algo_version=algo_version,
        database=database
    )
    
    successful_results = [r for r in results if r.get("status") == "success"]
    failed_results = [r for r in results if r.get("status") != "success"]
    
    # Log detailed statistics
    total_count = len(results)
    success_count = len(successful_results)
    failed_count = len(failed_results)
    
    ctx.info(f"MRD calculation complete: {success_count} samples processed successfully out of {total_count} total samples")
    if failed_count > 0:
        ctx.warning(f"Failed results: {failed_count} samples had errors")
    
    if successful_results:
        # Save results to CSV file
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mrd_dataset_results_{dataset}_{timestamp}"
            csv_path = save_data_to_csv(ctx, successful_results, filename)
            ctx.info(f"Results automatically saved to CSV: {csv_path}")
        except Exception as e:
            ctx.warning(f"Failed to save results to CSV: {str(e)}")
    else:
        ctx.warning(f"MRD calculation completed with errors for dataset {dataset}")
    
    # Add summary information to the first result for visibility
    if results:
        results[0]["_summary"] = {
            "total_samples": total_count,
            "successful_samples": success_count,
            "failed_samples": failed_count,
            "success_rate": f"{success_count}/{total_count}" if total_count > 0 else "0/0",
            "csv_path": csv_path
        }
    
    return results


@mcp.tool()
def list_dataset_samples(ctx: Context,
                        dataset: str,
                        run_name: Optional[str] = None, 
                        algo_version: Optional[str] = None,
                        database: str = "main") -> Dict[str, Any]:
    """
    Get a comprehensive list of all samples for a given dataset with optional filtering of algo_version and run_name.
    
    This tool queries the histograms_snv table to retrieve sample information, useful for:
    - Understanding dataset composition before MRD analysis
    - Identifying available samples and their metadata
    - Planning targeted analyses on specific subjects/samples
    
    AUTOMATIC CSV SAVING:
    Results are automatically saved to a CSV file in the 'outputs' directory with the filename format:
    'dataset_samples_{dataset}_{timestamp}.csv' (e.g., 'dataset_samples_DATASET_NAME_20250915_143022.csv')
    
    The CSV file contains all sample information with columns:
    - dataset, run_name, algo_version, subject, sample
    
    Save Location: ./outputs/ directory (created automatically if it doesn't exist)
    
    Usage Examples:
    - All samples: list_dataset_samples(dataset="DATASET_NAME")
    - Specific run: list_dataset_samples(dataset="DATASET_NAME", run_name="RUN_NAME")  
    - Specific algorithm: list_dataset_samples(dataset="DATASET_NAME", algo_version="main-YYYYMMDD")
    
    Args:
        dataset: Dataset name for partitioning (e.g., "DATASET_NAME") [REQUIRED]
        run_name: Optional run name filter (e.g., "RUN_NAME") [OPTIONAL]
        algo_version: Optional algorithm version filter (e.g., "main-YYYYMMDD") [OPTIONAL]
        database: Database containing the genomic data [OPTIONAL - default: "main"]
        
    Returns:
        Dict containing:
        - execution_id: Athena query execution ID
        - result_table: Formatted markdown table of samples
        - columns: ["dataset", "run_name", "algo_version", "subject", "sample"]  
        - rows: Sample data rows
        - row_count: Total number of samples found
        - csv_path: Path to the automatically saved CSV file (if successful)
    """
    # Build query with optional run_name and algo_version filters
    query = f"""
    SELECT DISTINCT h.dataset, h.run_name, h.algo_version, h.subject, h.sample
    FROM main.histograms_snv h
    WHERE h.dataset = '{dataset}'
    """
        
    if run_name:
        query += f"  AND h.run_name = '{run_name}'\n"
    
    if algo_version:
        query += f"  AND h.algo_version = '{algo_version}'\n"
    
    query += "ORDER BY h.dataset, h.run_name, h.algo_version, h.subject, h.sample"
    
    # Execute the query
    result = execute_query(ctx, query, database, wait_for_completion=True)
    
    # Save results to CSV if query was successful
    if result.get("status") == "SUCCEEDED" and result.get("rows"):
        try:
            # Create CSV filename with dataset and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dataset_samples_{dataset}_{timestamp}"
            
            # Convert rows to list of dictionaries for CSV saving
            columns = result.get("columns", [])
            rows = result.get("rows", [])
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            csv_path = save_data_to_csv(ctx, data, filename)
            ctx.info(f"Sample list automatically saved to CSV: {csv_path}")
            
            # Add CSV path to the result
            result["csv_path"] = csv_path
            
        except Exception as e:
            ctx.warning(f"Failed to save sample list to CSV: {str(e)}")
    
    return result


@mcp.prompt()
def get_mrd_baseline_instructions() -> str:
    """
    Load MRD Detection Rate Calculation baseline instructions for modification reference.
    Use when modifying or researching changes to the MRD process - all changes should reference this baseline.
    changes to the MRD process - all changes should reference this baseline.
    
    Returns:
        str: Complete MRD baseline instructions from markdown file
    """
    try:
        # Use the utility function with hardcoded MRD instructions filename
        instructions_content = read_instruction_file("mrd_detection_rate_calculation.md")
        
        # Return the raw content for prompt usage
        return instructions_content
        
    except Exception as e:
        error_msg = f"ERROR: Unable to load MRD baseline instructions - {str(e)}"
        return error_msg


@mcp.prompt()
def get_data_lake_query_instruction() -> str:
    """
    Load Data Lake query instructions for Athena database querying.
    Use when querying the Athena data lake to understand schema, available tables, 
    query patterns, and best practices for data lake analytics.
    
    Returns:
        str: Complete data lake query instructions from both schema and examples markdown files
    """
    try:
        # Load both data lake instruction files
        schema_content = read_instruction_file("data_lake/data_lake_schema.md")
        examples_content = read_instruction_file("data_lake/data_lake_query_examples.md")
        
        # Combine both files with clear separators
        combined_content = f"""# Data Lake Query Instructions

## Part 1: Database Schema Reference
{schema_content}

{'='*80}

## Part 2: Query Examples and Patterns
{examples_content}
"""
        
        # Return the combined content for prompt usage
        return combined_content
        
    except Exception as e:
        error_msg = f"ERROR: Unable to load data lake query instructions - {str(e)}"
        return error_msg


def main():
    mcp.run()

if __name__ == "__main__":
    main()