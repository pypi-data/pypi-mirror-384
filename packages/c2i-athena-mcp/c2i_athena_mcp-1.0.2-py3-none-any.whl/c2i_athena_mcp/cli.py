#!/usr/bin/env python
import os
import argparse
import json
import logging
from typing import Dict, Any

from .server import mcp

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Athena MCP server CLI."""
    parser = argparse.ArgumentParser(description="AWS Athena MCP Server")
    
    parser.add_argument("--region", help="AWS region", default=os.environ.get("AWS_REGION"))
    parser.add_argument("--s3-output", help="S3 output location", default=os.environ.get("S3_OUTPUT_LOCATION"))
    parser.add_argument("--profile", help="AWS profile name", default=os.environ.get("AWS_PROFILE"))
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--dev", help="Run in development mode with MCP inspector", action="store_true")
    
    args = parser.parse_args()
    
    # Load config from file if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return
    
    # Override with command line args
    if args.region:
        config['region_name'] = args.region
    if args.s3_output:
        config['s3_output_location'] = args.s3_output
    if args.profile:
        config['profile_name'] = args.profile
        
    # Get credentials from environment variables if not in config
    if 'aws_access_key_id' not in config:
        config['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID')
    if 'aws_secret_access_key' not in config:
        config['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # Validate required config
    if not config.get('s3_output_location'):
        logger.error("S3 output location is required")
        return
    
    if not (config.get('profile_name') or (config.get('aws_access_key_id') and config.get('aws_secret_access_key'))):
        logger.error("Either AWS profile or access key/secret key pair is required")
        return
    
    # Run the server
    mcp.run(config=config)

if __name__ == "__main__":
    main()