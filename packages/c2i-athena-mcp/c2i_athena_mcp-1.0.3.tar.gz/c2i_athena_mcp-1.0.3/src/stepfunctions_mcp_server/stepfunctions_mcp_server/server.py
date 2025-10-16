import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import boto3
import time
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# Import the MCP server library
from mcp.server.fastmcp import FastMCP, Context

# Import the Step Functions client
from stepfunctions_mcp_server.stepfunctions_client import StepFunctionsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dictionary to store execution IDs for tracking
executions = {}

# Environment variable names
AWS_REGION = "AWS_REGION"
AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
AWS_SESSION_TOKEN = "AWS_SESSION_TOKEN"
AWS_PROFILE = "AWS_PROFILE"

@dataclass
class AppContext:
    stepfunctions_client: StepFunctionsClient

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup using environment variables    
    region_name = os.environ.get(AWS_REGION)
    aws_access_key_id = os.environ.get(AWS_ACCESS_KEY_ID)
    aws_secret_access_key = os.environ.get(AWS_SECRET_ACCESS_KEY)
    aws_session_token = os.environ.get(AWS_SESSION_TOKEN)
    profile_name = os.environ.get(AWS_PROFILE)
    
    logger.info(f"Initializing Step Functions client with region: {region_name}")
    logger.info(f"Using AWS profile: {profile_name if profile_name else 'No profile specified'}")
    
    stepfunctions_client = StepFunctionsClient(
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        profile_name=profile_name
    )
    try:
        yield AppContext(stepfunctions_client=stepfunctions_client)
    finally:
        # Cleanup on shutdown
        # Any cleanup code if needed
        pass

# Create the MCP Server with lifespan
mcp = FastMCP("AWS Step Functions", 
              dependencies=["boto3", "pandas", "mcp>=0.1.0"],
              lifespan=app_lifespan)

# Resource endpoints
@mcp.resource("state-machines://")
async def get_state_machines() -> str:
    """List all available state machines in AWS Step Functions"""
    # Access context through the request's state
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    stepfunctions_client = state.lifespan_context.stepfunctions_client
    
    machines = stepfunctions_client.list_state_machines()
    
    formatted_output = "# Available State Machines\n\n"
    formatted_output += "| Name | ARN | Type | Creation Date |\n"
    formatted_output += "| ---- | --- | ---- | ------------ |\n"
    
    for machine in machines:
        formatted_output += f"| {machine['name']} | {machine['stateMachineArn']} | {machine['type']} | {machine['creationDate']} |\n"
    
    return formatted_output

@mcp.resource("state-machine://{machine_arn}")
async def get_state_machine_details(machine_arn: str) -> str:
    """Get details for a specific state machine"""
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    stepfunctions_client = state.lifespan_context.stepfunctions_client
    
    machine = stepfunctions_client.describe_state_machine(machine_arn)
    
    formatted_output = f"# State Machine: {machine.get('name')}\n\n"
    formatted_output += f"- **ARN**: {machine.get('stateMachineArn')}\n"
    formatted_output += f"- **Type**: {machine.get('type')}\n"
    formatted_output += f"- **Created**: {machine.get('creationDate')}\n"
    formatted_output += f"- **Role ARN**: {machine.get('roleArn')}\n\n"
    
    formatted_output += "## State Machine Definition\n\n"
    formatted_output += "```json\n"
    formatted_output += json.dumps(json.loads(machine.get('definition', '{}')), indent=2)
    formatted_output += "\n```\n"
    
    return formatted_output

@mcp.resource("executions://{machine_arn}")
async def get_executions(machine_arn: str) -> str:
    """List executions for a state machine"""
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    stepfunctions_client = state.lifespan_context.stepfunctions_client
    
    executions_list = stepfunctions_client.list_executions(machine_arn)
    
    formatted_output = f"# Executions for State Machine\n\n"
    formatted_output += "| Execution Name | ARN | Status | Start Date | Stop Date |\n"
    formatted_output += "| -------------- | --- | ------ | ---------- | --------- |\n"
    
    for execution in executions_list:
        stop_date = execution.get('stopDate', 'Running')
        formatted_output += f"| {execution.get('name', 'N/A')} | {execution.get('executionArn')} | {execution.get('status')} | {execution.get('startDate')} | {stop_date} |\n"
    
    return formatted_output

@mcp.resource("execution://{execution_arn}")
async def get_execution_details(execution_arn: str) -> str:
    """Get details for a specific execution"""
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    stepfunctions_client = state.lifespan_context.stepfunctions_client
    
    execution = stepfunctions_client.describe_execution(execution_arn)
    
    formatted_output = f"# Execution Details\n\n"
    formatted_output += f"- **Name**: {execution.get('name', 'N/A')}\n"
    formatted_output += f"- **ARN**: {execution.get('executionArn')}\n"
    formatted_output += f"- **State Machine ARN**: {execution.get('stateMachineArn')}\n"
    formatted_output += f"- **Status**: {execution.get('status')}\n"
    formatted_output += f"- **Started**: {execution.get('startDate')}\n"
    
    if 'stopDate' in execution:
        formatted_output += f"- **Stopped**: {execution.get('stopDate')}\n"
    
    formatted_output += "\n## Input\n\n"
    formatted_output += "```json\n"
    formatted_output += json.dumps(json.loads(execution.get('input', '{}')), indent=2)
    formatted_output += "\n```\n\n"
    
    formatted_output += "## Output\n\n"
    if execution.get('output'):
        formatted_output += "```json\n"
        formatted_output += json.dumps(json.loads(execution.get('output', '{}')), indent=2)
        formatted_output += "\n```\n"
    else:
        formatted_output += "No output available yet.\n"
    
    return formatted_output

@mcp.resource("execution-history://{execution_arn}")
async def get_execution_history(execution_arn: str) -> str:
    """Get execution history for a specific execution"""
    from mcp.server.fastmcp import get_request_state
    state = get_request_state()
    stepfunctions_client = state.lifespan_context.stepfunctions_client
    
    events = stepfunctions_client.get_execution_history(execution_arn)
    
    formatted_output = f"# Execution History\n\n"
    formatted_output += "| Timestamp | Event Type | Details |\n"
    formatted_output += "| --------- | ---------- | ------- |\n"
    
    for event in events:
        # Extract details based on event type
        details = ""
        event_type = event.get('type')
        
        # Filter out common fields that are already displayed
        filtered_event = {k: v for k, v in event.items() if k not in ['id', 'type', 'timestamp']}
        
        details = json.dumps(filtered_event)
        if len(details) > 50:
            details = details[:50] + "..."
            
        formatted_output += f"| {event.get('timestamp')} | {event_type} | {details} |\n"
    
    return formatted_output

@mcp.resource("history://")
async def get_execution_history() -> str:
    """Get history of tracked executions"""
    if not executions:
        return "No execution history available"
        
    formatted_output = "# Recent Step Functions Executions\n\n"
    
    for exec_id, details in sorted(
        executions.items(), 
        key=lambda x: x[1].get('timestamp', ''), 
        reverse=True
    )[:10]:
        formatted_output += f"- **ID**: {exec_id}\n"
        formatted_output += f"- **Status**: {details.get('status', 'Unknown')}\n"
        formatted_output += f"- **Time**: {details.get('timestamp', 'Unknown')}\n"
        formatted_output += f"- **State Machine**: {details.get('stateMachineArn', 'Unknown')}\n\n"
        
    return formatted_output

# Tool endpoints
@mcp.tool()
def list_state_machines(ctx: Context) -> List[Dict[str, Any]]:
    """List all available state machines in AWS Step Functions"""
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    return stepfunctions_client.list_state_machines()

@mcp.tool()
def get_state_machine(ctx: Context, state_machine_arn: str) -> Dict[str, Any]:
    """
    Get details about a specific state machine.
    
    Args:
        state_machine_arn: The ARN of the state machine
        
    Returns:
        State machine details
    """
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    return stepfunctions_client.describe_state_machine(state_machine_arn)

@mcp.tool()
def create_state_machine(
    ctx: Context, 
    name: str, 
    definition: str, 
    role_arn: str
) -> Dict[str, Any]:
    """
    Create a new state machine.
    
    Args:
        name: The name of the state machine
        definition: The Amazon States Language definition (JSON)
        role_arn: The ARN of the IAM role for the state machine
        
    Returns:
        Details of the created state machine including ARN
    """
    global executions
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    ctx.info(f"Creating state machine '{name}'...")
    
    try:
        machine_arn = stepfunctions_client.create_state_machine(name, definition, role_arn)
        
        # Get full state machine details
        machine_details = stepfunctions_client.describe_state_machine(machine_arn)
        
        ctx.info(f"Successfully created state machine: {name}")
        return {
            "stateMachineArn": machine_arn,
            "name": name,
            "status": "CREATED",
            "message": f"State machine '{name}' created successfully",
            "details": machine_details
        }
    except Exception as e:
        ctx.warning(f"Failed to create state machine: {str(e)}")
        return {
            "name": name,
            "status": "ERROR",
            "message": f"Failed to create state machine: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def update_state_machine(
    ctx: Context,
    state_machine_arn: str,
    definition: str = None,
    role_arn: str = None
) -> Dict[str, Any]:
    """
    Update an existing state machine.
    
    Args:
        state_machine_arn: The ARN of the state machine
        definition: New Amazon States Language definition (optional)
        role_arn: New IAM role ARN (optional)
        
    Returns:
        Update details
    """
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    # At least one parameter must be specified
    if definition is None and role_arn is None:
        return {
            "stateMachineArn": state_machine_arn,
            "status": "ERROR",
            "message": "Either definition or role_arn must be specified for update"
        }
    
    ctx.info(f"Updating state machine {state_machine_arn}...")
    
    try:
        result = stepfunctions_client.update_state_machine(
            state_machine_arn=state_machine_arn,
            definition=definition,
            role_arn=role_arn
        )
        
        update_details = []
        if definition:
            update_details.append("definition")
        if role_arn:
            update_details.append("role")
            
        ctx.info(f"State machine updated successfully: {', '.join(update_details)}")
        
        return {
            "stateMachineArn": state_machine_arn,
            "status": "UPDATED",
            "message": f"State machine updated successfully: {', '.join(update_details)}",
            "updateDate": result.get('updateDate')
        }
    except Exception as e:
        ctx.warning(f"Failed to update state machine: {str(e)}")
        return {
            "stateMachineArn": state_machine_arn,
            "status": "ERROR",
            "message": f"Failed to update state machine: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def delete_state_machine(ctx: Context, state_machine_arn: str) -> Dict[str, Any]:
    """
    Delete a state machine.
    
    Args:
        state_machine_arn: The ARN of the state machine to delete
        
    Returns:
        Delete operation result
    """
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    ctx.info(f"Deleting state machine {state_machine_arn}...")
    
    try:
        stepfunctions_client.delete_state_machine(state_machine_arn)
        
        ctx.info(f"State machine deleted successfully")
        return {
            "stateMachineArn": state_machine_arn,
            "status": "DELETED",
            "message": "State machine deleted successfully"
        }
    except Exception as e:
        ctx.warning(f"Failed to delete state machine: {str(e)}")
        return {
            "stateMachineArn": state_machine_arn,
            "status": "ERROR",
            "message": f"Failed to delete state machine: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def start_execution(
    ctx: Context, 
    state_machine_arn: str, 
    input_data: str = None,
    execution_name: str = None
) -> Dict[str, Any]:
    """
    Start execution of a state machine.
    
    Args:
        state_machine_arn: The ARN of the state machine
        input_data: JSON input data for the execution (optional)
        execution_name: Custom name for the execution (optional)
        
    Returns:
        Execution details
    """
    global executions
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    ctx.info(f"Starting execution of state machine {state_machine_arn}...")
    
    try:
        result = stepfunctions_client.start_execution(
            state_machine_arn=state_machine_arn,
            input_data=input_data,
            name=execution_name
        )
        
        execution_arn = result.get('executionArn')
        
        # Store in tracking dictionary
        executions[execution_arn] = {
            "status": "RUNNING",
            "timestamp": datetime.now().isoformat(),
            "stateMachineArn": state_machine_arn
        }
        
        ctx.info(f"Execution started successfully with ARN: {execution_arn}")
        return {
            "executionArn": execution_arn,
            "status": "RUNNING",
            "startDate": result.get('startDate'),
            "message": f"Execution started successfully with ARN: {execution_arn}"
        }
    except Exception as e:
        ctx.warning(f"Failed to start execution: {str(e)}")
        return {
            "stateMachineArn": state_machine_arn,
            "status": "ERROR",
            "message": f"Failed to start execution: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def describe_execution(ctx: Context, execution_arn: str) -> Dict[str, Any]:
    """
    Get details about a state machine execution.
    
    Args:
        execution_arn: The ARN of the execution
        
    Returns:
        Execution details
    """
    global executions
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    try:
        details = stepfunctions_client.describe_execution(execution_arn)
        
        # Update status in our tracking dictionary
        if execution_arn in executions:
            executions[execution_arn]["status"] = details.get('status')
        
        ctx.info(f"Retrieved execution details for {execution_arn}")
        return details
    except Exception as e:
        ctx.warning(f"Failed to describe execution {execution_arn}: {str(e)}")
        return {
            "executionArn": execution_arn,
            "status": "ERROR",
            "message": f"Failed to describe execution: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def list_executions(
    ctx: Context, 
    state_machine_arn: str,
    status_filter: str = None
) -> Dict[str, Any]:
    """
    List executions for a state machine.
    
    Args:
        state_machine_arn: The ARN of the state machine
        status_filter: Optional filter by status (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
        
    Returns:
        List of executions
    """
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    try:
        executions_list = stepfunctions_client.list_executions(
            state_machine_arn=state_machine_arn,
            status_filter=status_filter
        )
        
        status_info = f" with status '{status_filter}'" if status_filter else ""
        ctx.info(f"Listed {len(executions_list)} executions{status_info}")
        
        return {
            "stateMachineArn": state_machine_arn,
            "status": "SUCCESS",
            "executions": executions_list,
            "count": len(executions_list),
            "message": f"Retrieved {len(executions_list)} executions{status_info}"
        }
    except Exception as e:
        ctx.warning(f"Failed to list executions: {str(e)}")
        return {
            "stateMachineArn": state_machine_arn,
            "status": "ERROR",
            "message": f"Failed to list executions: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def stop_execution(
    ctx: Context, 
    execution_arn: str,
    error: str = None,
    cause: str = None
) -> Dict[str, Any]:
    """
    Stop a running state machine execution.
    
    Args:
        execution_arn: The ARN of the execution to stop
        error: Optional error code
        cause: Optional cause description
        
    Returns:
        Stop operation result
    """
    global executions
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    ctx.info(f"Stopping execution {execution_arn}...")
    
    try:
        result = stepfunctions_client.stop_execution(
            execution_arn=execution_arn,
            error=error,
            cause=cause
        )
        
        # Update status in our tracking dictionary
        if execution_arn in executions:
            executions[execution_arn]["status"] = "STOPPED"
        
        ctx.info(f"Execution stopped successfully")
        return {
            "executionArn": execution_arn,
            "status": "STOPPED",
            "stopDate": result.get('stopDate'),
            "message": "Execution stopped successfully"
        }
    except Exception as e:
        ctx.warning(f"Failed to stop execution: {str(e)}")
        return {
            "executionArn": execution_arn,
            "status": "ERROR",
            "message": f"Failed to stop execution: {str(e)}",
            "error": str(e)
        }

@mcp.tool()
def get_execution_history(ctx: Context, execution_arn: str) -> Dict[str, Any]:
    """
    Get the event history of a state machine execution.
    
    Args:
        execution_arn: The ARN of the execution
        
    Returns:
        Execution history events
    """
    stepfunctions_client = ctx.request_context.lifespan_context.stepfunctions_client
    
    try:
        events = stepfunctions_client.get_execution_history(execution_arn)
        
        ctx.info(f"Retrieved {len(events)} events from execution history")
        return {
            "executionArn": execution_arn,
            "status": "SUCCESS",
            "events": events,
            "eventCount": len(events),
            "message": f"Retrieved {len(events)} events from execution history"
        }
    except Exception as e:
        ctx.warning(f"Failed to get execution history: {str(e)}")
        return {
            "executionArn": execution_arn,
            "status": "ERROR",
            "message": f"Failed to get execution history: {str(e)}",
            "error": str(e)
        }

# Create sample prompts to guide users
@mcp.prompt()
def list_state_machines_prompt() -> str:
    """Shows how to list all state machines"""
    return """You can list all available state machines in AWS Step Functions using the list_state_machines tool. Here's an example:

To list all state machines:
1. Use the list_state_machines tool without any parameters
2. Review the returned list of state machine information

Alternatively, you can access the state-machines resource using "state-machines://" to get a formatted list."""


@mcp.prompt()
def state_machine_definition_guide() -> str:
    """Guide for writing Amazon States Language definitions"""
    return """# Amazon States Language Guide

Amazon States Language (ASL) is a JSON-based language used to define state machines in AWS Step Functions.

## Basic State Machine Structure

```json
{
  "Comment": "A description of the state machine",
  "StartAt": "FirstState",
  "States": {
    "FirstState": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME",
      "Next": "SecondState"
    },
    "SecondState": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.result",
          "StringEquals": "success",
          "Next": "SuccessState"
        }
      ],
      "Default": "FailState"
    },
    "SuccessState": {
      "Type": "Succeed"
    },
    "FailState": {
      "Type": "Fail",
      "Error": "ErrorCode",
      "Cause": "Error description"
    }
  }
}
```

## Common State Types

### Task State
Executes an AWS service like Lambda or a specific activity.
```json
"TaskState": {
  "Type": "Task",
  "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME",
  "Next": "NextState",
  "Retry": [
    {
      "ErrorEquals": ["States.ALL"],
      "IntervalSeconds": 1,
      "MaxAttempts": 3,
      "BackoffRate": 2.0
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Next": "ErrorHandlingState"
    }
  ]
}
```

### Choice State
Adds branching logic to your state machine.
```json
"ChoiceState": {
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.condition",
      "BooleanEquals": true,
      "Next": "TrueState"
    },
    {
      "Variable": "$.condition",
      "BooleanEquals": false,
      "Next": "FalseState"
    }
  ],
  "Default": "DefaultState"
}
```

### Parallel State
Executes branches in parallel.
```json
"ParallelState": {
  "Type": "Parallel",
  "Branches": [
    {
      "StartAt": "Branch1State",
      "States": {
        "Branch1State": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME_1",
          "End": true
        }
      }
    },
    {
      "StartAt": "Branch2State",
      "States": {
        "Branch2State": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME_2",
          "End": true
        }
      }
    }
  ],
  "Next": "NextState"
}
```

### Map State
Runs a set of steps for each element in an array.
```json
"MapState": {
  "Type": "Map",
  "ItemsPath": "$.array",
  "Iterator": {
    "StartAt": "IteratorState",
    "States": {
      "IteratorState": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME",
        "End": true
      }
    }
  },
  "Next": "NextState"
}
```

### Wait State
Delays execution for a specified time.
```json
"WaitState": {
  "Type": "Wait",
  "Seconds": 10,
  "Next": "NextState"
}
```

### Succeed and Fail States
Terminal states that end execution.
```json
"SucceedState": {
  "Type": "Succeed"
},
"FailState": {
  "Type": "Fail",
  "Error": "ErrorCode",
  "Cause": "Error description"
}
```"""

def main():
    mcp.run()

if __name__ == "__main__":
    main()
