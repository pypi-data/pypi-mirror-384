# -*- coding: utf-8 -*-

"""
AWS Kinesis Data Streams client wrapper.

This module provides a high-level interface for interacting with AWS Kinesis,
including single and batch record operations with automatic retry logic.
"""

import json
from time import sleep
from typing import Any, Dict, List, Optional

from core_mixins.utils import get_batches

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException


class KinesisClient(AwsClient):
    """
    Client for AWS Kinesis Data Streams.

    This client provides methods for writing records to Kinesis data streams,
    supporting both single and batch operations. Includes intelligent retry
    logic for handling transient failures and throughput exceeded errors.

    Example:
        .. code-block:: python

            # Initialize client
            kinesis = KinesisClient(region="us-east-1")

            # Put single record
            response = kinesis.put_record(
                stream_name="my-stream",
                data=b'{"event": "user_signup", "user_id": 123}',
                partition_key="user-123"
            )
            print(f"Shard: {response['ShardId']}")

            # Put multiple records with retry
            records = [
                {"event": "login", "user_id": 1},
                {"event": "purchase", "user_id": 2}
            ]
            kinesis.send_records(
                records=records,
                stream_name="my-stream",
                partition_key="events"
            )
        ..
    """

    client: "mypy_boto3_kinesis.client.KinesisClient"  # type: ignore[name-defined]

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the Kinesis client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """

        super().__init__("kinesis", region_name=region, **kwargs)

    def create_stream(
        self,
        stream_name: str,
        shard_count: Optional[int] = None,
        stream_mode_details: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a new Kinesis data stream with specified capacity. Creates either
        a provisioned stream (with explicit shard count) or an on-demand stream
        (auto-scaling). Stream becomes ACTIVE within seconds and can start
        accepting data immediately.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/client/create_stream.html

        :param stream_name:
            Name of the stream to create. Must be:
            - 1-128 characters long
            - Alphanumeric, hyphens, underscores, and periods only
            - Cannot use "aws:" prefix (reserved)
            - Unique within the AWS account and region

        :param shard_count:
            Number of shards for provisioned capacity mode. Each shard provides:
            - Write: 1 MB/sec or 1,000 records/sec
            - Read: 2 MB/sec or 5 read transactions/sec

            Required for provisioned mode, must be None for on-demand mode.
            Can be increased/decreased later using UpdateShardCount API.

        :param stream_mode_details:
            Stream capacity mode configuration. Dict with single key:

            - **StreamMode** (str): Capacity mode, either:
                - "PROVISIONED": Fixed shard count (requires shard_count parameter)
                - "ON_DEMAND": Auto-scaling capacity (shard_count must be None)

            Default behavior if omitted:
                - With shard_count: Creates provisioned stream
                - Without shard_count: Creates on-demand stream

        :param kwargs:
            Additional boto3 parameters:

            - **Tags** (dict): Resource tags for the stream. Dictionary of key-value pairs:
              {"Environment": "Production", "Application": "Analytics"}

        :return:
            Empty dictionary on success. Stream creation is asynchronous.
            Use describe_stream() or wait_until_active() to check status.

        :raises AwsClientException:
            If stream creation fails (e.g., name already exists, invalid parameters,
            resource limits exceeded).

        Example:
            .. code-block:: python

                kinesis = KinesisClient(region="us-east-1")

                # Create provisioned stream with 2 shards
                kinesis.create_stream(
                    stream_name="my-stream",
                    shard_count=2
                )

                # Create on-demand stream (auto-scaling)
                kinesis.create_stream(
                    stream_name="my-on-demand-stream",
                    stream_mode_details={"StreamMode": "ON_DEMAND"}
                )

                # Create stream with explicit mode specification
                kinesis.create_stream(
                    stream_name="my-provisioned-stream",
                    shard_count=5,
                    stream_mode_details={"StreamMode": "PROVISIONED"}
                )

                # Create stream with tags
                kinesis.create_stream(
                    stream_name="tagged-stream",
                    shard_count=1,
                    Tags={
                        "Environment": "Production",
                        "Application": "Analytics",
                        "CostCenter": "Engineering"
                    }
                )

                # Wait for stream to become active
                waiter = kinesis.client.get_waiter('stream_exists')
                waiter.wait(StreamName="my-stream")

                print("Stream is now active and ready to use")
            ..

        Note:
          - Stream creation is asynchronous (completes in seconds)
          - Provisioned mode: Fixed cost based on shard hours
          - On-demand mode: Pay per GB ingested/retrieved, auto-scales
          - Default retention: 24 hours (configurable up to 365 days)
          - Maximum 50 streams per region by default (soft limit)
          - Stream name must be unique within account and region
        """

        create_kwargs: Dict[str, Any] = {"StreamName": stream_name}

        # Add shard count for provisioned mode
        if shard_count is not None:
            create_kwargs["ShardCount"] = shard_count

        # Add stream mode details if specified
        if stream_mode_details:
            create_kwargs["StreamModeDetails"] = stream_mode_details

        # Add any additional kwargs (like Tags)
        create_kwargs.update(kwargs)

        try:
            return self.client.create_stream(**create_kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def put_record(
        self,
        stream_name: str,
        data: bytes,
        partition_key: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Write a single data record to a Kinesis data stream. Sends one
        record at a time for real-time ingestion. Each shard supports up
        to 1,000 records/second with a maximum write throughput
        of 1 MiB/second.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/client/put_record.html

        :param stream_name: Name of the Kinesis data stream.

        :param data:
            Data payload (bytes). Base64-encoded when serialized. Maximum size:
            1 MiB (including partition key).

        :param partition_key:
            Key determining which shard receives the record. Records with the
            same partition key go to the same shard.

        :param kwargs:
            Additional boto3 parameters:

            - **ExplicitHashKey** (str): Hash value to explicitly determine
              target shard, overriding partition key hash.
            - **SequenceNumberForOrdering** (str): Guarantees strictly increasing
              sequence numbers from same client/partition key.

        :return:
            Dictionary containing shard placement information:

            .. code-block:: python

                {
                    "ShardId": "shardId-000000000001",
                    "SequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "EncryptionType": "NONE" | "KMS"
                }
            ..

        :raises AwsClientException: If record write fails.

        Example:
            .. code-block:: python

                kinesis = KinesisClient(region="us-east-1")

                # Put single record
                response = kinesis.put_record(
                    stream_name="clickstream",
                    data=b'{"event": "page_view", "page": "/home"}',
                    partition_key="user-123"
                )
                print(f"Written to {response['ShardId']}")

                # With explicit hash key
                kinesis.put_record(
                    stream_name="orders",
                    data=b'{"order_id": "12345"}',
                    partition_key="order-12345",
                    ExplicitHashKey="123456789"
                )
            ..
        """

        try:
            return self.client.put_record(
                StreamName=stream_name,
                Data=data,
                PartitionKey=partition_key,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def put_records(
        self,
        stream_name: str,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Write multiple data records to a Kinesis data stream in a single
        request. Batch operation for writing up to 500 records at once. More
        efficient than multiple `put_record()` calls. Each record can be up to 1 MiB,
        with a total request limit of 5 MiB including partition keys. Each shard
        supports up to 1,000 records/second with 1 MiB/second throughput.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/client/put_records.html

        :param stream_name: Name of the Kinesis data stream.

        :param records:
            List of record dictionaries (max 500). Each record structure:

            .. code-block:: python

                {
                    "Data": b"bytes",  # Required: The data blob (base64-encoded)
                    "PartitionKey": "string",  # Required: Determines shard
                    "ExplicitHashKey": "string"  # Optional: Override partition key hash
                }
            ..

        :return:
            Dictionary containing batch operation results:

            .. code-block:: python

                {
                    "FailedRecordCount": 0,  # Number of failed records
                    "Records": [
                        {
                            "SequenceNumber": "string",
                            "ShardId": "string",
                            "ErrorCode": "string",  # Present if failed
                            "ErrorMessage": "string"  # Present if failed
                        },
                    ],
                    "EncryptionType": "NONE" | "KMS"
                }
            ..

        :raises AwsClientException: If the batch write operation fails.

        Example:
            .. code-block:: python

                kinesis = KinesisClient(region="us-east-1")

                # Prepare batch records
                records = [
                    {
                        "Data": b'{"event": "login", "user_id": 1}',
                        "PartitionKey": "user-1"
                    },
                    {
                        "Data": b'{"event": "purchase", "user_id": 2}',
                        "PartitionKey": "user-2"
                    }
                ]

                # Put records
                response = kinesis.put_records(
                    stream_name="events",
                    records=records
                )

                # Check for failures
                if response["FailedRecordCount"] > 0:
                    for i, record in enumerate(response["Records"]):
                        if "ErrorCode" in record:
                            print(f"Record {i} failed: {record['ErrorMessage']}")
            ..

        Note:
            For automatic retry logic with failed records, use `send_records()`
            instead, which handles transient failures and throughput exceeded errors.
        """

        try:
            return self.client.put_records(
                Records=records,
                StreamName=stream_name,
            )

        except Exception as error:
            raise AwsClientException(error) from error

    def send_records(
        self,
        records: List[Dict[str, Any]],
        stream_name: str,
        partition_key: str,
        records_per_request: int = 500,
        max_attempts: int = 10,
        interval_between_attempt: int = 1,
    ) -> None:
        """
        Send records to Kinesis with automatic retry logic. High-level wrapper
        around `put_records()` that automatically handles transient failures and
        throughput exceeded errors. Converts Python dictionaries to JSON,
        batches records, and retries failed records with exponential backoff.

        :param records:
            List of record dictionaries to send. Each dict will be JSON-serialized.
            Example: [{"event": "login", "user_id": 123}, ...]

        :param stream_name: Name of the target Kinesis data stream.

        :param partition_key:
            Partition key for all records. All records will be sent to the
            same shard based on this key.

        :param records_per_request:
            Maximum number of records per batch request. Default: 500 (AWS maximum).

        :param max_attempts:
            Maximum retry attempts for failed records. Default: 10.

        :param interval_between_attempt:
            Base delay in seconds between retry attempts. Uses exponential backoff
            (delay = interval * attempt_number). Default: 1 second.

        :raises AwsClientException:
            If records still fail after max_attempts retries.

        Example:
            .. code-block:: python

                kinesis = KinesisClient(region="us-east-1")

                # Send event records with automatic retry
                events = [
                    {"event": "login", "user_id": 123, "timestamp": "2024-01-01T10:00:00Z"},
                    {"event": "purchase", "user_id": 456, "amount": 99.99},
                    {"event": "logout", "user_id": 123}
                ]

                kinesis.send_records(
                    records=events,
                    stream_name="user-events",
                    partition_key="events"
                )

                # With custom retry settings
                kinesis.send_records(
                    records=events,
                    stream_name="critical-events",
                    partition_key="events",
                    records_per_request=100,  # Smaller batches
                    max_attempts=20,  # More retries
                    interval_between_attempt=2  # Longer delays
                )
            ..

        Note:
            - Records are automatically JSON-serialized using `json.dumps()`
            - Failed records are automatically retried with exponential backoff
            - Delay between retries: 1s, 2s, 3s, 4s, ... (interval * attempt)
            - All records use the same partition key (same shard)
        """

        self._send_to_kinesis_stream(
            stream_name=stream_name,
            records=[
                {
                    "Data": json.dumps(record),
                    "PartitionKey": partition_key
                } for record in records
            ],
            records_per_request=records_per_request,
            interval_between_attempt=interval_between_attempt,
            max_attempts=max_attempts,
        )

    def _send_to_kinesis_stream(
        self,
        records: List[Dict[str, Any]],
        stream_name: str,
        records_per_request: int = 500,
        max_attempts: int = 10,
        interval_between_attempt: int = 1,
    ) -> None:
        """
        Internal implementation for sending records with retry logic.

        Handles batching, retry logic with exponential backoff, and error tracking.
        Called by `send_records()` to perform the actual data transfer. This method
        splits large record sets into batches and retries failed records automatically.

        :param records:
            List of formatted record dictionaries ready for Kinesis API.

            .. code-block:: python

                [{
                    "Data": b"bytes",  # JSON-serialized data (bytes or string)
                    "PartitionKey": "string",  # Required
                    "ExplicitHashKey": "string"  # Optional
                }]
            ..

        :param stream_name: Name of the Kinesis data stream.

        :param records_per_request:
            Number of records per batch (max 500). Default: 500.

        :param max_attempts:
            Maximum retry attempts for failed records. Default: 10.

        :param interval_between_attempt:
            Base interval in seconds for exponential backoff. Default: 1.

        :raises AwsClientException:
            If any records still fail after max_attempts retries.

        Algorithm:

            1. Split records into batches of `records_per_request` size
            2. For each batch:

               a. Send to Kinesis using `put_records()`
               b. Check for failed records in response
               c. If failures exist and attempts remain:

                  - Wait: interval * attempt_number seconds
                  - Extract only failed records
                  - Retry the failed records

               d. Repeat until success or max_attempts reached

            3. Raise exception if any records still failed

        Note:
            - This is an internal method. Use `send_records()` instead.
            - Uses exponential backoff: 1s, 2s, 3s, 4s, 5s, ...
            - Only retries records that actually failed (not entire batch)
        """

        if not records:
            return

        for chunk_ in get_batches(records, records_per_request):
            res = self.put_records(stream_name, chunk_)
            attempt = 1

            while res.get("FailedRecordCount", 0) > 0 and attempt <= max_attempts:
                sleep(interval_between_attempt * attempt)

                # Only retry records that failed (have ErrorCode in the response)...
                chunk_ = [
                    chunk_[x] for x, data in enumerate(res.get("Records", []))
                    if data.get("ErrorCode", False)
                ]

                res = self.put_records(stream_name, chunk_)
                attempt += 1

            if res["FailedRecordCount"] > 0:
                raise AwsClientException("Failed sending data to Kinesis!")
