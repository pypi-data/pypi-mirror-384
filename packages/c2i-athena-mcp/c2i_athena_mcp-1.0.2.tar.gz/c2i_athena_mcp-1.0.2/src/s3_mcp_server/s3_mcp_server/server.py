import os
import logging
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP, Context
from .s3_client import S3Client
import argparse

# Global prefix variables
PREFIX_READ = None
PREFIX_WRITE = None

# MCP server instance
def get_s3_client():
    return S3Client()

mcp = FastMCP(
    "AWS S3",
    dependencies=["boto3", "mcp>=0.1.0"],
)

def check_read_prefix(path: str):
    if PREFIX_READ and not path.startswith(PREFIX_READ):
        raise ValueError(f"Read operation not allowed outside prefix: {PREFIX_READ}")

def check_write_prefix(path: str):
    if PREFIX_WRITE and not path.startswith(PREFIX_WRITE):
        raise ValueError(f"Write operation not allowed outside prefix: {PREFIX_WRITE}")

@mcp.tool()
def list_objects(ctx: Context, bucket: str = "", prefix: str = "") -> List[str]:
    """
    List S3 objects in a bucket with an optional prefix.
    If no bucket is provided, lists available buckets.
    
    Args:
        ctx: The context object
        bucket: S3 bucket name
        prefix: Optional prefix to filter objects
        
    Returns:
        Comma-separated list of objects or buckets
    """
    if not bucket or bucket == "":
        if PREFIX_READ is None:
            s3 = get_s3_client()
            return "Available buckets: " + ','.join(s3.list_buckets())
        else:
            raise ValueError(f"Bucket name required when read prefix is restricted")
    check_read_prefix(prefix)
    s3 = get_s3_client()
    return ','.join(s3.list_objects(bucket, prefix))

@mcp.tool()
def cp(ctx: Context, source: str, destination: str, recursive: bool = False, extra_args: List[str] = None) -> str:
    """
    Copy files between S3 or between S3 and local filesystem.
    
    Args:
        ctx: The context object
        source: Source location (s3:// or local path)
        destination: Destination location (s3:// or local path)
        recursive: Whether to copy recursively
        extra_args: Additional arguments for the S3 operation, including --exclude/--include
        
    Returns:
        Result message of the copy operation
    """
    # Check prefixes for read and write
    if source.startswith("s3://"):
        check_read_prefix(source)
    if destination.startswith("s3://"):
        check_write_prefix(destination)
    s3 = get_s3_client()
    return s3.cp(source, destination, recursive, extra_args)

@mcp.tool()
def mv(ctx: Context, source: str, destination: str, recursive: bool = False, extra_args: List[str] = None) -> str:
    """
    Move files between S3 or between S3 and local filesystem.
    
    Args:
        ctx: The context object
        source: Source location (s3:// or local path)
        destination: Destination location (s3:// or local path)
        recursive: Whether to move recursively
        extra_args: Additional arguments for the S3 operation, including --exclude/--include
        
    Returns:
        Result message of the move operation
    """
    if source.startswith("s3://"):
        check_write_prefix(source)
    if destination.startswith("s3://"):
        check_write_prefix(destination)
    s3 = get_s3_client()
    return s3.mv(source, destination, recursive, extra_args)

@mcp.tool()
def rm(ctx: Context, target: str, recursive: bool = False, extra_args: List[str] = None) -> str:
    """
    Remove files from S3.
    
    Args:
        ctx: The context object
        target: S3 path to remove
        recursive: Whether to delete recursively
        extra_args: Additional arguments for the S3 operation, including --exclude/--include
        
    Returns:
        Result message of the remove operation
    """
    if target.startswith("s3://"):
        check_write_prefix(target)
    s3 = get_s3_client()
    return s3.rm(target, recursive, extra_args)

@mcp.tool()
def sync(ctx: Context, source: str, destination: str, extra_args: List[str] = None) -> str:
    """
    Sync directories between S3 or between S3 and local filesystem.
    
    Args:
        ctx: The context object
        source: Source location (s3:// or local path)
        destination: Destination location (s3:// or local path)
        extra_args: Additional arguments for the S3 operation, including --exclude/--include
        
    Returns:
        Result message of the sync operation
    """
    if source.startswith("s3://"):
        check_read_prefix(source)
    if destination.startswith("s3://"):
        check_write_prefix(destination)
    s3 = get_s3_client()
    return s3.sync(source, destination, extra_args)

@mcp.tool()
def mb(ctx: Context, bucket_uri: str, extra_args: List[str] = None) -> str:
    """
    Make a new S3 bucket.
    
    Args:
        ctx: The context object
        bucket_uri: URI of the bucket to create (s3://bucket-name)
        extra_args: Additional arguments for the S3 operation
        
    Returns:
        Result message of the make bucket operation
    """
    check_write_prefix(bucket_uri)
    s3 = get_s3_client()
    return s3.mb(bucket_uri, extra_args)

@mcp.tool()
def rb(ctx: Context, bucket_uri: str, extra_args: List[str] = None) -> str:
    """
    Remove an S3 bucket.
    
    Args:
        ctx: The context object
        bucket_uri: URI of the bucket to remove (s3://bucket-name)
        extra_args: Additional arguments for the S3 operation
        
    Returns:
        Result message of the remove bucket operation
    """
    check_write_prefix(bucket_uri)
    s3 = get_s3_client()
    return s3.rb(bucket_uri, extra_args)

def main():
    global PREFIX_READ, PREFIX_WRITE
    parser = argparse.ArgumentParser(description="AWS S3 MCP Server")
    parser.add_argument("--prefix-read", type=str, default=None, help="Restrict read operations to this S3 prefix")
    parser.add_argument("--prefix-write", type=str, default=None, help="Restrict write operations to this S3 prefix")
    args = parser.parse_args()
    PREFIX_READ = args.prefix_read
    PREFIX_WRITE = args.prefix_write
    mcp.run()

if __name__ == "__main__":
    main()
