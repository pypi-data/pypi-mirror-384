"""
Examples for using the AWS Athena MCP server.

This module demonstrates how to use the AWS Athena MCP server programmatically.
"""

import json
import os
from typing import Dict, Any, Optional

from .server import mcp


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file or use environment variables.
    
    Args:
        config_path: Path to a JSON configuration file (optional)
        
    Returns:
        Configuration dictionary
    """
    config = {}
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Override or set from environment variables
    if os.environ.get("AWS_REGION"):
        config['region_name'] = os.environ.get("AWS_REGION")
    if os.environ.get("S3_OUTPUT_LOCATION"):
        config['s3_output_location'] = os.environ.get("S3_OUTPUT_LOCATION")
    if os.environ.get("AWS_PROFILE"):
        config['profile_name'] = os.environ.get("AWS_PROFILE")
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        config['aws_access_key_id'] = os.environ.get("AWS_ACCESS_KEY_ID")
    if os.environ.get("AWS_SECRET_ACCESS_KEY"):
        config['aws_secret_access_key'] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    return config


def run_server(config_path: Optional[str] = None) -> None:
    """
    Run the AWS Athena MCP server with configuration.
    
    Args:
        config_path: Path to a JSON configuration file (optional)
    """
    config = load_config(config_path)
    
    # Validate required config
    if not config.get('s3_output_location'):
        raise ValueError("S3 output location is required in configuration")
    
    if not (config.get('profile_name') or (config.get('aws_access_key_id') and config.get('aws_secret_access_key'))):
        raise ValueError("Either AWS profile or access key/secret key pair is required in configuration")
    
    # Run the server
    mcp.run(config=config)


def run_development_server(config_path: Optional[str] = None) -> None:
    """
    Run the AWS Athena MCP server in development mode with the MCP Inspector.
    
    Args:
        config_path: Path to a JSON configuration file (optional)
    """
    from mcp.cli.dev import dev_command
    import sys
    
    config = load_config(config_path)
    
    # Validate required config
    if not config.get('s3_output_location'):
        raise ValueError("S3 output location is required in configuration")
    
    if not (config.get('profile_name') or (config.get('aws_access_key_id') and config.get('aws_secret_access_key'))):
        raise ValueError("Either AWS profile or access key/secret key pair is required in configuration")
        
    # Run in development mode
    sys.argv = ["mcp", "dev", "--config", json.dumps(config)]
    dev_command()


if __name__ == "__main__":
    # Example usage
    run_development_server("../config.json")