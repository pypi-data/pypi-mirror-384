import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class StepFunctionsClient:
    """Client wrapper for AWS Step Functions operations"""

    def __init__(
        self,
        region_name=None,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
        profile_name=None
    ):
        """
        Initialize a Step Functions client.
        
        :param region_name: The AWS region to connect to.
        :param aws_access_key_id: The AWS access key ID to use for authentication.
        :param aws_secret_access_key: The AWS secret access key to use for authentication.
        :param aws_session_token: The AWS session token for temporary credentials.
        :param profile_name: The AWS profile name to use for authentication.
        """
        client_kwargs = {}

        if region_name:
            client_kwargs['region_name'] = region_name
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs['aws_access_key_id'] = aws_access_key_id
            client_kwargs['aws_secret_access_key'] = aws_secret_access_key
            if aws_session_token:
                client_kwargs['aws_session_token'] = aws_session_token

        # Create a session and client
        self.stepfunctions_client = boto3.client('stepfunctions', **client_kwargs)
        logger.info(f"Initialized Step Functions client in region: {region_name or 'default'}")

    def list_state_machines(self) -> List[Dict[str, Any]]:
        """
        List all state machines in the account.
        
        :return: List of state machines
        """
        try:
            state_machines = []
            paginator = self.stepfunctions_client.get_paginator('list_state_machines')
            
            for page in paginator.paginate():
                for machine in page.get('stateMachines', []):
                    state_machines.append({
                        'name': machine['name'],
                        'stateMachineArn': machine['stateMachineArn'],
                        'type': machine['type'],
                        'creationDate': machine['creationDate'].isoformat()
                    })
                    
            return state_machines
        except ClientError as e:
            logger.error(f"Error listing state machines: {e}")
            raise

    def describe_state_machine(self, state_machine_arn: str) -> Dict[str, Any]:
        """
        Get details about a specific state machine.
        
        :param state_machine_arn: The ARN of the state machine to describe
        :return: Details about the state machine
        """
        try:
            response = self.stepfunctions_client.describe_state_machine(
                stateMachineArn=state_machine_arn
            )
            
            # Convert datetime objects to ISO format strings for JSON serialization
            if 'creationDate' in response:
                response['creationDate'] = response['creationDate'].isoformat()
            
            return response
        except ClientError as e:
            logger.error(f"Error describing state machine {state_machine_arn}: {e}")
            raise

    def create_state_machine(self, name: str, definition: str, role_arn: str) -> str:
        """
        Create a new state machine.
        
        :param name: The name of the state machine
        :param definition: The Amazon States Language definition
        :param role_arn: The ARN of the IAM role for the state machine
        :return: The ARN of the created state machine
        """
        try:
            response = self.stepfunctions_client.create_state_machine(
                name=name,
                definition=definition,
                roleArn=role_arn
            )
            return response['stateMachineArn']
        except ClientError as e:
            logger.error(f"Error creating state machine {name}: {e}")
            raise

    def update_state_machine(self, state_machine_arn: str, definition: str = None, role_arn: str = None) -> Dict[str, Any]:
        """
        Update an existing state machine.
        
        :param state_machine_arn: The ARN of the state machine to update
        :param definition: The new Amazon States Language definition
        :param role_arn: The new IAM role ARN for the state machine
        :return: Response from the update operation
        """
        kwargs = {'stateMachineArn': state_machine_arn}
        
        if definition is not None:
            kwargs['definition'] = definition
            
        if role_arn is not None:
            kwargs['roleArn'] = role_arn
            
        try:
            response = self.stepfunctions_client.update_state_machine(**kwargs)
            return response
        except ClientError as e:
            logger.error(f"Error updating state machine {state_machine_arn}: {e}")
            raise

    def delete_state_machine(self, state_machine_arn: str) -> Dict[str, Any]:
        """
        Delete a state machine.
        
        :param state_machine_arn: The ARN of the state machine to delete
        :return: Response from the delete operation
        """
        try:
            response = self.stepfunctions_client.delete_state_machine(
                stateMachineArn=state_machine_arn
            )
            return response
        except ClientError as e:
            logger.error(f"Error deleting state machine {state_machine_arn}: {e}")
            raise

    def start_execution(self, state_machine_arn: str, input_data: str = None, name: str = None) -> Dict[str, Any]:
        """
        Start execution of a state machine.
        
        :param state_machine_arn: The ARN of the state machine to execute
        :param input_data: The JSON input data for the execution
        :param name: Optional custom name for the execution
        :return: Details of the started execution including the execution ARN
        """
        try:
            kwargs = {'stateMachineArn': state_machine_arn}
            
            if input_data is not None:
                kwargs['input'] = input_data
                
            if name is not None:
                kwargs['name'] = name
                
            response = self.stepfunctions_client.start_execution(**kwargs)
            
            # Convert datetime objects to ISO format strings for JSON serialization
            if 'startDate' in response:
                response['startDate'] = response['startDate'].isoformat()
                
            return {
                'executionArn': response['executionArn'],
                'startDate': response.get('startDate')
            }
        except ClientError as e:
            logger.error(f"Error starting execution of state machine {state_machine_arn}: {e}")
            raise

    def describe_execution(self, execution_arn: str) -> Dict[str, Any]:
        """
        Get details about a state machine execution.
        
        :param execution_arn: The ARN of the execution to describe
        :return: Details about the execution
        """
        try:
            response = self.stepfunctions_client.describe_execution(
                executionArn=execution_arn
            )
            
            # Convert datetime objects to ISO format strings for JSON serialization
            for date_field in ['startDate', 'stopDate']:
                if date_field in response:
                    response[date_field] = response[date_field].isoformat()
                    
            return response
        except ClientError as e:
            logger.error(f"Error describing execution {execution_arn}: {e}")
            raise

    def list_executions(self, state_machine_arn: str, status_filter: str = None) -> List[Dict[str, Any]]:
        """
        List executions for a state machine.
        
        :param state_machine_arn: The ARN of the state machine
        :param status_filter: Optional filter by status (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
        :return: List of executions
        """
        try:
            executions = []
            kwargs = {'stateMachineArn': state_machine_arn}
            
            if status_filter:
                kwargs['statusFilter'] = status_filter
                
            paginator = self.stepfunctions_client.get_paginator('list_executions')
            
            for page in paginator.paginate(**kwargs):
                for execution in page.get('executions', []):
                    # Convert datetime objects to ISO format strings
                    for date_field in ['startDate', 'stopDate']:
                        if date_field in execution:
                            execution[date_field] = execution[date_field].isoformat()
                            
                    executions.append(execution)
                    
            return executions
        except ClientError as e:
            logger.error(f"Error listing executions for state machine {state_machine_arn}: {e}")
            raise

    def stop_execution(self, execution_arn: str, error: str = None, cause: str = None) -> Dict[str, Any]:
        """
        Stop a running state machine execution.
        
        :param execution_arn: The ARN of the execution to stop
        :param error: Optional error code for the stopped execution
        :param cause: Optional cause message for the stopped execution
        :return: Response from the stop operation
        """
        try:
            kwargs = {'executionArn': execution_arn}
            
            if error:
                kwargs['error'] = error
                
            if cause:
                kwargs['cause'] = cause
                
            response = self.stepfunctions_client.stop_execution(**kwargs)
            
            # Convert datetime objects to ISO format strings
            if 'stopDate' in response:
                response['stopDate'] = response['stopDate'].isoformat()
                
            return response
        except ClientError as e:
            logger.error(f"Error stopping execution {execution_arn}: {e}")
            raise

    def get_execution_history(self, execution_arn: str) -> List[Dict[str, Any]]:
        """
        Get the execution history of a state machine execution.
        
        :param execution_arn: The ARN of the execution
        :return: List of events in the execution history
        """
        try:
            events = []
            paginator = self.stepfunctions_client.get_paginator('get_execution_history')
            
            for page in paginator.paginate(executionArn=execution_arn):
                for event in page.get('events', []):
                    # Convert datetime objects to ISO format strings
                    if 'timestamp' in event:
                        event['timestamp'] = event['timestamp'].isoformat()
                        
                    events.append(event)
                    
            return events
        except ClientError as e:
            logger.error(f"Error getting execution history for {execution_arn}: {e}")
            raise
