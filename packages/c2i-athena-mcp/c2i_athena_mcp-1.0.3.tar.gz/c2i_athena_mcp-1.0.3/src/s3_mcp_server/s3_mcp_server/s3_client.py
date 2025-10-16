import boto3
import subprocess
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class S3Client:
    """
    Client for interacting with AWS S3 using boto3 and AWS CLI.
    """
    def __init__(self, region_name: Optional[str] = None):
        self.region_name = region_name or os.getenv("AWS_REGION")
        self.s3 = boto3.client("s3", region_name=self.region_name)

    def list_buckets(self) -> List[str]:
        response = self.s3.list_buckets()
        return [b["Name"] for b in response.get("Buckets", [])]

    def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        paginator = self.s3.get_paginator("list_objects_v2")
        result = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                result.append(obj["Key"])
        return result

    def run_cli(self, args: List[str]) -> str:
        cmd = ["aws", "s3"] + args
        logger.info(f"Running CLI: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(result.stderr)
            raise RuntimeError(result.stderr)
        return result.stdout

    def cp(self, source: str, destination: str, recursive: bool = False, extra_args: List[str] = None) -> str:
        args = ["cp", source, destination]
        if recursive:
            args.append("--recursive")
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)

    def mv(self, source: str, destination: str, recursive: bool = False, extra_args: List[str] = None) -> str:
        args = ["mv", source, destination]
        if recursive:
            args.append("--recursive")
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)

    def rm(self, target: str, recursive: bool = False, extra_args: List[str] = None) -> str:
        args = ["rm", target]
        if recursive:
            args.append("--recursive")
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)

    def sync(self, source: str, destination: str, extra_args: List[str] = None) -> str:
        args = ["sync", source, destination]
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)

    def mb(self, bucket_uri: str, extra_args: List[str] = None) -> str:
        args = ["mb", bucket_uri]
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)

    def rb(self, bucket_uri: str, extra_args: List[str] = None) -> str:
        args = ["rb", bucket_uri]
        if extra_args:
            args.extend(extra_args)
        return self.run_cli(args)
