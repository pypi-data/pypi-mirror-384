import datetime
import time

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from aws_vibe_guru.aws_sqs import read_aws_credentials


def create_cloudwatch_logs_connection(access_key=None, secret_key=None, region=None):
    if not all([access_key, secret_key, region]):
        credentials = read_aws_credentials()
        access_key = access_key or credentials["access_key"]
        secret_key = secret_key or credentials["secret_key"]
        region = region or credentials["region"]

    try:
        return boto3.client(
            "logs",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
    except NoCredentialsError as e:
        raise ValueError("Invalid AWS credentials provided") from e
    except ClientError as e:
        raise ValueError(f"Failed to connect to AWS CloudWatch Logs: {e}") from e


def list_log_groups(log_group_prefix=None, max_results=50):
    try:
        logs_client = create_cloudwatch_logs_connection()

        kwargs = {"limit": min(max_results, 50)}
        if log_group_prefix:
            kwargs["logGroupNamePrefix"] = log_group_prefix

        log_groups = []
        next_token = None

        while True:
            if next_token:
                kwargs["nextToken"] = next_token

            response = logs_client.describe_log_groups(**kwargs)

            for log_group in response.get("logGroups", []):
                log_groups.append(
                    {
                        "name": log_group["logGroupName"],
                        "creation_time": datetime.datetime.fromtimestamp(log_group["creationTime"] / 1000).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "stored_bytes": log_group.get("storedBytes", 0),
                        "retention_days": log_group.get("retentionInDays", "Never expire"),
                    }
                )

                if len(log_groups) >= max_results:
                    break

            if len(log_groups) >= max_results:
                break

            next_token = response.get("nextToken")
            if not next_token:
                break

        return log_groups

    except ClientError as e:
        raise ValueError(f"Failed to list log groups: {e}") from e


def search_lambda_logs(
    lambda_name,
    search_terms,
    hours=24,
    max_results=100,
):
    try:
        logs_client = create_cloudwatch_logs_connection()

        log_group_name = f"/aws/lambda/{lambda_name}"

        try:
            logs_client.describe_log_groups(logGroupNamePrefix=log_group_name, limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise ValueError(f"Log group '{log_group_name}' not found") from e
            raise

        end_time = int(time.time() * 1000)
        start_time = end_time - (hours * 3600 * 1000)

        if isinstance(search_terms, str):
            search_terms = [search_terms]

        all_results = []

        for term in search_terms:
            filter_pattern = f'"{term}"'

            try:
                response = logs_client.filter_log_events(
                    logGroupName=log_group_name,
                    startTime=start_time,
                    endTime=end_time,
                    filterPattern=filter_pattern,
                    limit=max_results,
                )

                for event in response.get("events", []):
                    all_results.append(
                        {
                            "timestamp": datetime.datetime.fromtimestamp(event["timestamp"] / 1000).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "message": event["message"],
                            "log_stream": event["logStreamName"],
                            "search_term": term,
                        }
                    )

                next_token = response.get("nextToken")
                while next_token and len(all_results) < max_results:
                    response = logs_client.filter_log_events(
                        logGroupName=log_group_name,
                        startTime=start_time,
                        endTime=end_time,
                        filterPattern=filter_pattern,
                        nextToken=next_token,
                        limit=max_results - len(all_results),
                    )

                    for event in response.get("events", []):
                        all_results.append(
                            {
                                "timestamp": datetime.datetime.fromtimestamp(event["timestamp"] / 1000).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "message": event["message"],
                                "log_stream": event["logStreamName"],
                                "search_term": term,
                            }
                        )

                    next_token = response.get("nextToken")

            except ClientError as e:
                if e.response["Error"]["Code"] == "InvalidParameterException":
                    continue
                raise

        all_results.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "log_group": log_group_name,
            "lambda_name": lambda_name,
            "search_terms": search_terms,
            "hours": hours,
            "total_results": len(all_results),
            "results": all_results[:max_results],
        }

    except ClientError as e:
        raise ValueError(f"Failed to search lambda logs: {e}") from e


def get_recent_lambda_logs(lambda_name, hours=1, max_results=50):
    try:
        logs_client = create_cloudwatch_logs_connection()

        log_group_name = f"/aws/lambda/{lambda_name}"

        try:
            logs_client.describe_log_groups(logGroupNamePrefix=log_group_name, limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise ValueError(f"Log group '{log_group_name}' not found") from e
            raise

        end_time = int(time.time() * 1000)
        start_time = end_time - (hours * 3600 * 1000)

        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            limit=max_results,
        )

        results = []
        for event in response.get("events", []):
            results.append(
                {
                    "timestamp": datetime.datetime.fromtimestamp(event["timestamp"] / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "message": event["message"],
                    "log_stream": event["logStreamName"],
                }
            )

        next_token = response.get("nextToken")
        while next_token and len(results) < max_results:
            response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                nextToken=next_token,
                limit=max_results - len(results),
            )

            for event in response.get("events", []):
                results.append(
                    {
                        "timestamp": datetime.datetime.fromtimestamp(event["timestamp"] / 1000).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "message": event["message"],
                        "log_stream": event["logStreamName"],
                    }
                )

            next_token = response.get("nextToken")

        results.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "log_group": log_group_name,
            "lambda_name": lambda_name,
            "hours": hours,
            "total_results": len(results),
            "results": results[:max_results],
        }

    except ClientError as e:
        raise ValueError(f"Failed to get lambda logs: {e}") from e
