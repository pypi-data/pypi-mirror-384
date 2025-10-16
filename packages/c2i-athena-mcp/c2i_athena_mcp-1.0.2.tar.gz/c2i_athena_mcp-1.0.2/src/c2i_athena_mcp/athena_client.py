import boto3
import time
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import os
import logging

logger = logging.getLogger(__name__)

class AthenaClient:
    """
    Client for interacting with AWS Athena.
    """
    
    def __init__(
        self,
        s3_output_location: str = None,
    ):
        """
        Initialize the Athena client.
        
        Args:
            region_name: AWS region name
            s3_output_location: S3 bucket location for query results
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            profile_name: AWS profile name
        """
        # Read from environment variables if not provided
        self.s3_output_location = s3_output_location or os.getenv("AWS_S3_OUTPUT_URI")
        region_name = os.getenv("AWS_REGION")
        
        self.athena_client = boto3.client('athena', region_name=region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        
    def list_databases(self) -> List[str]:
        """
        List all available databases in Athena.
        
        Returns:
            List of database names
        """
        response = self.athena_client.list_databases(
            CatalogName='AwsDataCatalog'
        )
        
        return [db["Name"] for db in response.get("DatabaseList", [])]
    
    def list_tables(self, database_name: str) -> List[str]:
        """
        List all tables in a database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            List of table names
        """
        response = self.athena_client.list_table_metadata(
            CatalogName='AwsDataCatalog',
            DatabaseName=database_name
        )
        
        return [table["Name"] for table in response.get("TableMetadataList", [])]
    
    def get_table_schema(self, database_name: str, table_name: str) -> List[Dict[str, str]]:
        """
        Get the schema of a table.
        
        Args:
            database_name: Name of the database
            table_name: Name of the table
            
        Returns:
            List of dictionaries with column names and types, including partition columns
        """
        response = self.athena_client.get_table_metadata(
            CatalogName='AwsDataCatalog',
            DatabaseName=database_name,
            TableName=table_name
        )
        
        table_metadata = response.get("TableMetadata", {})
        schema = [{"name": col["Name"], "type": col["Type"]} for col in table_metadata.get("Columns", [])]
        schema += [{"name": col["Name"], "type": col["Type"], "is_partition": True} for col in table_metadata.get("PartitionKeys", [])]
        
        return schema
    
    def execute_query(
        self, 
        query: str, 
        database: str = None,
        wait: bool = True,
        max_execution_time: int = 300,
    ) -> Dict[str, Any]:
        """
        Execute an Athena SQL query.
        
        Args:
            query: SQL query to execute
            database: Database name (optional)
            wait: Whether to wait for query completion
            max_execution_time: Maximum execution time in seconds
            
        Returns:
            Dictionary with query execution information
        """
        query_params = {
            'QueryString': query,
            'ResultConfiguration': {
                'OutputLocation': self.s3_output_location
            }
        }
        
        if database:
            query_params['QueryExecutionContext'] = {'Database': database}
            
        # Start the query execution
        response = self.athena_client.start_query_execution(**query_params)
        execution_id = response['QueryExecutionId']
        
        if wait:
            return self._wait_for_query(execution_id, max_execution_time)
        
        return {"execution_id": execution_id, "status": "SUBMITTED"}
    
    def _wait_for_query(self, execution_id: str, max_execution_time: int) -> Dict[str, Any]:
        """
        Wait for a query to complete.
        
        Args:
            execution_id: Query execution ID
            max_execution_time: Maximum execution time in seconds
            
        Returns:
            Dictionary with query information
        """
        start_time = time.time()
        while (time.time() - start_time) < max_execution_time:
            query_details = self.athena_client.get_query_execution(
                QueryExecutionId=execution_id
            )
            
            state = query_details['QueryExecution']['Status']['State']
            
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                if state == 'SUCCEEDED':
                    s3_path = query_details['QueryExecution']['ResultConfiguration']['OutputLocation']
                    return {
                        "execution_id": execution_id,
                        "status": state,
                        "s3_path": s3_path,
                        "statistics": query_details['QueryExecution'].get('Statistics', {})
                    }
                else:
                    reason = query_details['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
                    return {
                        "execution_id": execution_id,
                        "status": state,
                        "error_reason": reason
                    }
            
            # Wait before checking again
            time.sleep(2)
        
        # Timeout case
        self.athena_client.stop_query_execution(QueryExecutionId=execution_id)
        return {
            "execution_id": execution_id,
            "status": "TIMEOUT",
            "error_reason": f"Query execution time exceeded {max_execution_time} seconds"
        }
    
    def get_query_results(self, execution_id: str, max_results: int = None) -> Dict[str, Any]:
        """
        Get query results for a completed query.
        
        Args:
            execution_id: Query execution ID
            max_results: Maximum number of results to retrieve
            
        Returns:
            Dictionary with column names, types and rows
        """
        query_details = self.athena_client.get_query_execution(
            QueryExecutionId=execution_id
        )
        
        state = query_details['QueryExecution']['Status']['State']
        if state != 'SUCCEEDED':
            reason = query_details['QueryExecution']['Status'].get('StateChangeReason', 'Unknown reason')
            return {
                "execution_id": execution_id,
                "status": state,
                "error_reason": reason
            }
        
        # Get results - handle None max_results by using a reasonable default
        get_results_params = {
            'QueryExecutionId': execution_id
        }
        if max_results is not None:
            get_results_params['MaxResults'] = max_results
        
        results = self.athena_client.get_query_results(**get_results_params)
        
        # Extract column info and data
        column_info = []
        rows = []
        
        if results['ResultSet']['Rows']:
            # Extract column names from the first row
            header_row = results['ResultSet']['Rows'][0]
            columns = [item.get('VarCharValue', '') for item in header_row.get('Data', [])]
            
            # Get column types if available
            for metadata in results['ResultSet'].get('ResultSetMetadata', {}).get('ColumnInfo', []):
                column_info.append({
                    'name': metadata.get('Name', ''),
                    'type': metadata.get('Type', '')
                })
            
            # Skip the header row
            for row in results['ResultSet']['Rows'][1:]:
                row_data = []
                for item in row.get('Data', []):
                    row_data.append(item.get('VarCharValue', None))
                rows.append(row_data)
        
        return {
            "execution_id": execution_id,
            "status": "SUCCEEDED",
            "column_info": column_info,
            "columns": [col['name'] for col in column_info],
            "rows": rows,
            "row_count": len(rows)
        }
    
    def get_results_as_dataframe(self, execution_id: str, max_results: int) -> pd.DataFrame:
        """
        Get query results as a pandas DataFrame.
        
        Args:
            execution_id: Query execution ID
            max_results: Maximum number of results to retrieve
            
        Returns:
            Pandas DataFrame containing query results
        """
        results = self.get_query_results(execution_id, max_results)
        
        if results['status'] != 'SUCCEEDED':
            logger.error(f"Query failed with status {results['status']}: {results.get('error_reason', 'Unknown error')}")
            return pd.DataFrame()
        
        if not results.get('rows'):
            return pd.DataFrame(columns=results.get('columns', []))
        
        return pd.DataFrame(data=results['rows'], columns=results.get('columns', []))

    def get_query_results_with_summary(self, execution_id: str, max_results: int = None) -> Dict[str, Any]:
        """
        Get comprehensive execution summary including status, statistics, and results.
        
        This method provides unified result packaging that eliminates duplication across
        the server by combining query execution details, statistics, and formatted results.
        
        Args:
            execution_id: Query execution ID
            max_results: Maximum number of results to retrieve
            
        Returns:
            Dict containing:
            - execution_id: Query execution ID
            - status: "SUCCEEDED", "FAILED", "CANCELLED", etc.
            - message: Success/error message
            - columns: Column names (if successful)
            - rows: Result data rows (if successful)
            - row_count: Number of rows returned (if successful)
            - runtime_seconds: Query execution time (if successful)
            - data_scanned_mb: Amount of data processed (if successful)
            - data_scanned_bytes: Raw bytes scanned (if successful)
            - error_reason: Error details (if failed)
        """
        try:
            # Get query execution details first to check status
            query_details = self.athena_client.get_query_execution(
                QueryExecutionId=execution_id
            )
            
            state = query_details['QueryExecution']['Status']['State']
            
            if state == "SUCCEEDED":
                # Get results
                results = self.get_query_results(execution_id, max_results)
                
                if results["status"] == "SUCCEEDED":
                    # Extract runtime and data scanned information
                    execution_stats = query_details['QueryExecution'].get('Statistics', {})
                    runtime_ms = execution_stats.get('EngineExecutionTimeInMillis', 0)
                    runtime_seconds = round(runtime_ms / 1000, 2) if runtime_ms else 0
                    data_scanned_bytes = execution_stats.get('DataScannedInBytes', 0)
                    data_scanned_mb = round(data_scanned_bytes / (1024 * 1024), 2) if data_scanned_bytes else 0
                    
                    return {
                        "execution_id": execution_id,
                        "status": "SUCCEEDED",
                        "message": "Results retrieved successfully",
                        "columns": results.get("columns", []),
                        "rows": results.get("rows", []),
                        "row_count": results.get("row_count", 0),
                        "runtime_seconds": runtime_seconds,
                        "data_scanned_mb": data_scanned_mb,
                        "data_scanned_bytes": data_scanned_bytes
                    }
                else:
                    # Results retrieval failed despite successful execution
                    return {
                        "execution_id": execution_id,
                        "status": results["status"],
                        "message": f"Unable to get results: {results.get('error_reason', 'Unknown error')}",
                        "error_reason": results.get("error_reason", "Unknown error")
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
                # Still running or other state
                return {
                    "execution_id": execution_id,
                    "status": state,
                    "message": f"Query status: {state}"
                }
                
        except Exception as e:
            logger.error(f"Error getting execution summary for {execution_id}: {str(e)}")
            return {
                "execution_id": execution_id,
                "status": "ERROR",
                "message": f"Error retrieving execution summary: {str(e)}",
                "error_reason": str(e)
            }

    def execute_query_with_summary(self, query: str, database: str = None, max_results: int = None) -> Dict[str, Any]:
        """
        Execute a query and return comprehensive summary in one call.
        
        Convenience method that combines execute_query and get_query_results_with_summary
        to avoid the need for separate calls in application code.
        
        Args:
            query: SQL query to execute
            database: Database name (optional)
            max_results: Maximum number of results to retrieve
            
        Returns:
            Dict containing comprehensive execution summary including:
            - execution_id, status, message
            - columns, rows, row_count (if successful)
            - runtime_seconds, data_scanned_mb (if successful) 
            - error_reason (if failed)
        """
        try:
            # Execute the query first
            execution_result = self.execute_query(query, database, wait=True)
            
            if execution_result["status"] == "SUCCEEDED":
                # Get comprehensive results using the execution ID
                return self.get_query_results_with_summary(execution_result["execution_id"], max_results)
            else:
                # Return the error from query execution
                return {
                    "execution_id": execution_result.get("execution_id"),
                    "status": execution_result["status"], 
                    "message": f"Query execution failed: {execution_result.get('error_reason', 'Unknown error')}",
                    "error_reason": execution_result.get("error_reason", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error in execute_query_with_summary: {str(e)}")
            return {
                "execution_id": None,
                "status": "ERROR",
                "message": f"Error executing query: {str(e)}",
                "error_reason": str(e)
            }

if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv(dotenv_path="/home/ec2-user/code/athena_mcp_server/example.env", override=True)
    # Initialize AthenaClient
    athena_client = AthenaClient()
    databases = athena_client.list_databases()
    print(databases)