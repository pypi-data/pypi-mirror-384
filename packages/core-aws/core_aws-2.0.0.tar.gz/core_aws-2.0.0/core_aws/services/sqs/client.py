# -*- coding: utf-8 -*-

"""
AWS Simple Queue Service (SQS) client wrapper.

This module provides a high-level interface for interacting with AWS SQS,
including message sending, receiving, deletion, and batch operations.
"""

from typing import Any, Dict, Iterator, List

import boto3
from botocore.exceptions import ClientError
from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException
from core_mixins.utils import get_batches


class SqsClient(AwsClient):
    """
    Client for AWS Simple Queue Service (SQS).

    This client provides methods for sending, receiving, and deleting
    messages from SQS queues. It supports both single and batch operations,
    with automatic retry logic for failed deletions.

    Example:
        .. code-block:: python

            # Initialize client
            sqs = SqsClient(region="us-east-1")

            # Get a queue by name
            queue = sqs.get_queue_by_name("my-queue")

            # Send a message
            sqs.send_message(queue.url, "Hello, SQS!")

            # Receive messages
            messages = sqs.receive_messages(queue.url)
            for msg in messages:
                print(msg["Body"])
        ..
    """

    client: "mypy_boto3_sqs.client.SQSClient"  # type: ignore[name-defined]
    resource: Any  # boto3.resources.factory.sqs.ServiceResource

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the SQS client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """

        super().__init__("sqs", region_name=region, **kwargs)
        self.resource = boto3.resource("sqs", region_name=region, **kwargs)

    def create_queue(self, queue_name: str, **kwargs: Any) -> str:
        """
        Create a new SQS queue with the specified name and attributes. Creates
        a standard or FIFO queue. Queue names are limited to 80 characters including
        alphanumeric characters, hyphens (-), and underscores (_). FIFO queue names
        must end with the .fifo suffix.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/create_queue.html

        :param queue_name: Name of the queue to create (max 80 characters).

        :param kwargs:
            Additional boto3 parameters:

            - **Attributes** (dict): Queue configuration attributes:

                - **DelaySeconds** (str): Delivery delay in seconds (0-900). Default: 0.
                - **MaximumMessageSize** (str): Max message size in bytes (1024-262144). Default: 262144.
                - **MessageRetentionPeriod** (str): Message retention in seconds (60-1209600). Default: 345600 (4 days).
                - **ReceiveMessageWaitTimeSeconds** (str): Long-polling wait time (0-20). Default: 0.
                - **VisibilityTimeout** (str): Visibility timeout in seconds (0-43200). Default: 30.
                - **FifoQueue** (str): 'true' for FIFO queue, 'false' for standard. Default: 'false'.
                - **ContentBasedDeduplication** (str): 'true' to enable content-based deduplication (FIFO only).
                - **KmsMasterKeyId** (str): ID of AWS KMS key for server-side encryption.
                - **KmsDataKeyReusePeriodSeconds** (str): KMS key reuse period (60-86400). Default: 300.
                - **DeduplicationScope** (str): 'messageGroup' or 'queue' (high-throughput FIFO only).
                - **FifoThroughputLimit** (str): 'perQueue' or 'perMessageGroupId' (high-throughput FIFO only).
                - **RedrivePolicy** (str): JSON string defining dead-letter queue:

                  .. code-block:: python

                      {
                          "deadLetterTargetArn": "arn:aws:sqs:region:account:dlq-name",
                          "maxReceiveCount": "3"
                      }
                  ..

                - **RedriveAllowPolicy** (str): JSON string defining which source queues can use this as DLQ.

            - **tags** (dict): Key-value pairs to assign as queue tags.

        :return: The queue URL string (e.g., "https://sqs.region.amazonaws.com/account/queue-name").

        :raises AwsClientException: If queue creation fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Create a basic standard queue
                queue_url = sqs.create_queue(queue_name="my-queue")
                print(f"Queue URL: {queue_url}")

                # Create a FIFO queue with custom attributes
                queue_url = sqs.create_queue(
                    queue_name="my-queue.fifo",
                    Attributes={
                        "FifoQueue": "true",
                        "ContentBasedDeduplication": "true",
                        "MessageRetentionPeriod": "86400",  # 1 day
                        "VisibilityTimeout": "60"
                    }
                )

                # Create a queue with dead-letter queue
                queue_url = sqs.create_queue(
                    queue_name="my-main-queue",
                    Attributes={
                        "RedrivePolicy": json.dumps({
                            "deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:my-dlq",
                            "maxReceiveCount": "5"
                        }),
                        "VisibilityTimeout": "30"
                    },
                    tags={
                        "Environment": "production",
                        "Application": "my-app"
                    }
                )
            ..
        """

        try:
            response = self.client.create_queue(QueueName=queue_name, **kwargs)
            return response["QueueUrl"]

        except ClientError as error:
            raise AwsClientException(error) from error

    def get_queue_by_name(
        self,
        queue_name: str,
        **kwargs: Any
    ) -> "mypy_boto3_sqs.service_resource.Queue":  # type: ignore[name-defined]
        """
        Retrieve an existing Amazon SQS queue by name. Returns a Queue resource
        object that can be used to interact with the queue. To access a queue
        owned by another AWS account, use the `QueueOwnerAWSAccountId`
        parameter.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/service-resource/get_queue_by_name.html

        :param queue_name: The name of the queue.

        :param kwargs:
            Additional boto3 parameters:

            - **QueueOwnerAWSAccountId** (str):
                AWS account ID of the account that created the queue.
                Required for accessing queues in other accounts.

        :return:
            sqs.Queue resource object with the following attributes:

            - **url** (str): Queue URL (https://sqs.<region>.amazonaws.com/<account>/QueueName)
            - **dead_letter_source_queues**: Dead letter queue information
            - **meta**: Queue metadata
            - **attributes** (dict): Queue attributes dictionary:

            .. code-block:: python

                {
                    'QueueArn': 'arn:aws:sqs:...',
                    'ApproximateNumberOfMessages': '0',
                    'ApproximateNumberOfMessagesNotVisible': '0',
                    'ApproximateNumberOfMessagesDelayed': '0',
                    'CreatedTimestamp': '1699539978',
                    'LastModifiedTimestamp': '1699540164',
                    'VisibilityTimeout': '300',
                    'MaximumMessageSize': '262144',
                    'MessageRetentionPeriod': '3600',
                    'DelaySeconds': '60',
                    ...
                }
            ..

        :raises AwsClientException: If the queue cannot be retrieved.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Get a queue in same account
                queue = sqs.get_queue_by_name("my-queue")
                print(f"Queue URL: {queue.url}")

                # Get a queue in another account
                queue = sqs.get_queue_by_name(
                    "cross-account-queue",
                    QueueOwnerAWSAccountId="123456789012"
                )
            ..
        """

        try:
            return self.resource.get_queue_by_name(QueueName=queue_name, **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def send_message(
        self,
        queue_url: str,
        message: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send a single message to an SQS queue. Delivers a message to the
        specified queue. Messages can contain XML, JSON, or unformatted
        text. Allowed Unicode characters: #x9, #xA, #xD, #x20
        to #xD7FF, #xE000 to #xFFFD, #x10000 to #x10FFFF.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.send_message

        :param queue_url: URL of the SQS queue.
        :param message: Message body (up to 256 KB).

        :param kwargs:
            Additional boto3 parameters:

            - **DelaySeconds** (int): Delay before message becomes available (0-900 seconds).
            - **MessageAttributes** (dict): Custom attributes for the message.
            - **MessageDeduplicationId** (str): Deduplication ID for FIFO queues.
            - **MessageGroupId** (str): Message group ID for FIFO queues (required).

        :return: Dictionary containing MessageId, MD5OfMessageBody, and SequenceNumber.

        :raises AwsClientException: If message sending fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Send a simple message
                response = sqs.send_message(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    message="Hello, SQS!"
                )
                print(f"Message ID: {response['MessageId']}")

                # Send with delay and attributes
                sqs.send_message(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    message='{"event": "user_signup", "user_id": 123}',
                    DelaySeconds=30,
                    MessageAttributes={
                        "EventType": {
                            "StringValue": "UserSignup",
                            "DataType": "String"
                        }
                    }
                )
            ..
        """

        try:
            return self.client.send_message(
                QueueUrl=queue_url,
                MessageBody=message,
                **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def send_message_batch(
        self,
        queue_url: str,
        entries: List[Dict[str, Any]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send multiple messages to an SQS queue in a single request. Delivers up
        to 10 messages to the specified queue in a single batch operation. For FIFO
        queues, messages within a batch are enqueued in
        the order they are sent.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message_batch.html

        :param queue_url: URL of the SQS queue.

        :param entries:
            List of message entries (max 10). Each entry must contain:

            - **Id** (str): Unique identifier for the message (within batch).
            - **MessageBody** (str): Message content (up to 256 KB).
            - **DelaySeconds** (int, optional): Message delay (0-900 seconds).
            - **MessageAttributes** (dict, optional): Custom message attributes.
            - **MessageDeduplicationId** (str, optional): For FIFO queues.
            - **MessageGroupId** (str, optional): For FIFO queues.

        :param kwargs: Additional boto3 parameters.

        :return:
            Dictionary containing Successful and Failed lists:

            .. code-block:: python

                {
                    "Successful": [
                        {
                            "Id": "string",
                            "MessageId": "string",
                            "MD5OfMessageBody": "string",
                            "SequenceNumber": "string"
                        }
                    ],
                    "Failed": [
                        {
                            "Id": "string",
                            "SenderFault": True|False,
                            "Code": "string",
                            "Message": "string"
                        }
                    ]
                }
            ..

        :raises AwsClientException: If batch sending fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Send multiple messages
                response = sqs.send_message_batch(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    entries=[
                        {
                            "Id": "msg1",
                            "MessageBody": "First message"
                        },
                        {
                            "Id": "msg2",
                            "MessageBody": "Second message",
                            "DelaySeconds": 10
                        },
                        {
                            "Id": "msg3",
                            "MessageBody": "Third message"
                        }
                    ]
                )
                print(f"Successful: {len(response['Successful'])}")
                print(f"Failed: {len(response['Failed'])}")
            ..
        """

        try:
            return self.client.send_message_batch(
                QueueUrl=queue_url,
                Entries=entries,
                **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def receive_messages(
        self,
        queue_url: str,
        max_number_of_msg: int = 10,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Receive one or more messages from an SQS queue. Retrieves up to 10
        messages from the specified queue. Use the `WaitTimeSeconds` parameter
        to enable long-polling (recommended for reducing empty
        receives and API costs).

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html

        :param queue_url: URL of the SQS queue.
        :param max_number_of_msg: Maximum number of messages to retrieve (1-10). Default: 10.

        :param kwargs:
            Additional boto3 parameters:

            - **AttributeNames** (list): System attributes to retrieve (e.g., ['All', 'ApproximateReceiveCount']).
            - **MessageAttributeNames** (list): Custom message attributes to retrieve (e.g., ['All']).
            - **VisibilityTimeout** (int): Duration message is hidden after retrieval (0-43200 seconds).
            - **WaitTimeSeconds** (int): Long-polling wait time (0-20 seconds).

        :return:
            List of message dictionaries:

            .. code-block:: python

                [
                    {
                        "MessageId": "string",
                        "ReceiptHandle": "string",
                        "MD5OfBody": "string",
                        "Body": "string",
                        "Attributes": {
                            "ApproximateReceiveCount": "1",
                            "SentTimestamp": "1699539978000"
                        },
                        "MD5OfMessageAttributes": "string",
                        "MessageAttributes": {
                            "AttributeName": {
                                "StringValue": "string",
                                "BinaryValue": b"bytes",
                                "DataType": "String"
                            }
                        }
                    }
                ]
            ..

        :raises AwsClientException: If message retrieval fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Basic receive
                messages = sqs.receive_messages(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue"
                )
                for msg in messages:
                    print(f"Message: {msg['Body']}")

                # Long-polling with attributes
                messages = sqs.receive_messages(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    max_number_of_msg=5,
                    WaitTimeSeconds=20,  # Long-poll for 20 seconds
                    MessageAttributeNames=['All'],
                    AttributeNames=['All']
                )
            ..
        """

        try:
            return self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_number_of_msg,
                **kwargs).get("Messages", [])

        except ClientError as error:
            raise AwsClientException(error) from error

    def retrieve_all_messages(
        self,
        queue_url: str,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Retrieve all messages from a queue using an iterator. Continuously polls
        the queue and yields messages until the queue is empty. Useful for processing
        all messages in a queue.

        :param queue_url: URL of the SQS queue.
        :param kwargs: Additional parameters passed to `receive_messages()`.

        :return: Iterator yielding message dictionaries.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Process all messages in queue
                for message in sqs.retrieve_all_messages(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    WaitTimeSeconds=5
                ):
                    print(f"Processing: {message['Body']}")
                    # Process the message...
                    sqs.delete_message(queue_url, message['ReceiptHandle'])
            ..

        Warning:
            This method will continue until the queue is empty. Make sure
            to delete messages after processing to avoid infinite loops.
        """

        while True:
            messages = self.receive_messages(queue_url=queue_url, **kwargs)
            if not messages:
                break

            yield from messages

    def delete_message(
        self,
        queue_url: str,
        receipt_handle: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Delete a single message from an SQS queue. Deletes the specified
        message using its ReceiptHandle (not MessageId). Messages are automatically
        deleted after the retention period expires. Amazon SQS can delete a
        message even if it's locked by visibility timeout.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/delete_message.html

        :param queue_url: URL of the SQS queue.
        :param receipt_handle: Receipt handle of the message (from receive_message).
        :param kwargs: Additional boto3 parameters.

        :return: Empty dictionary on success.

        :raises AwsClientException: If message deletion fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Receive and delete a message
                messages = sqs.receive_messages(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue"
                )
                for msg in messages:
                    # Process the message...
                    print(msg['Body'])

                    # Delete after processing
                    sqs.delete_message(
                        queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                        receipt_handle=msg['ReceiptHandle']
                    )
            ..
        """

        try:
            return self.client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def delete_message_batch(
        self,
        queue_url: str,
        entries: List[Dict[str, str]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Delete multiple messages from an SQS queue in a single request. Deletes up
        to 10 messages in a single batch operation. Each entry
        must include the message Id and ReceiptHandle.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/delete_message_batch.html

        :param queue_url: URL of the SQS queue.

        :param entries:
            List of message entries to delete (max 10). Each entry must contain:

            - **Id** (str): Unique identifier for this deletion (within batch).
            - **ReceiptHandle** (str): Receipt handle from receive_message.

        :param kwargs: Additional boto3 parameters.

        :return:
            Dictionary containing Successful and Failed lists:

            .. code-block:: python

                {
                    "Successful": [
                        {
                            "Id": "string"
                        }
                    ],
                    "Failed": [
                        {
                            "Id": "string",
                            "SenderFault": True|False,
                            "Code": "string",
                            "Message": "string"
                        }
                    ]
                }
            ..

        :raises AwsClientException: If batch deletion fails.

        Example:
            .. code-block:: python

                sqs = SqsClient(region="us-east-1")

                # Receive messages
                messages = sqs.receive_messages(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue"
                )

                # Delete in batch
                delete_entries = [
                    {
                        "Id": msg['MessageId'],
                        "ReceiptHandle": msg['ReceiptHandle']
                    }
                    for msg in messages
                ]

                result = sqs.delete_message_batch(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123/my-queue",
                    entries=delete_entries
                )
                print(f"Deleted: {len(result['Successful'])}")
                print(f"Failed: {len(result['Failed'])}")
            ..
        """

        try:
            return self.client.delete_message_batch(
                QueueUrl=queue_url,
                Entries=entries,
                **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def delete_messages(
        self,
        queue_url: str,
        entries: List[Dict[str, str]],
        retries: int = 3,
        **kwargs
    ) -> Dict:
        """
        It's a wrapper over "delete_message_batch" and will delete all messages, if a
        message deletion fails it will be re-tried until success or until the
        maximum attempts are exhausted...

        :param queue_url: The SQS queue url.
        :param entries: The messages reference to delete.
        :param retries: Number of re-tries in case of errors while deleting the messages.
        :param kwargs: Other arguments to pass to delete_message_batch method.

        :return:

            .. code-block:: python

                {
                    "Successful": [{
                        "Id": "string"
                    }],
                    "Failed": [{
                        "Id": "string",
                        "SenderFault": True|False,
                        "Code": "string",
                        "Message": "string"
                    }]
                }
            ..
        """

        successful = []

        def _delete_batch(messages: List[Dict]) -> List[Dict]:
            failures_: List[Dict] = []

            for batch_ in get_batches(messages, 10):
                output = self.delete_message_batch(
                    queue_url=queue_url,
                    entries=batch_,
                    **kwargs)

                successful.extend(output.get("Successful", []))
                failures_.extend(output.get("Failed", []))

            return failures_

        failed = [rec["Id"] for rec in _delete_batch(entries)]
        entries = [record for record in entries if record["Id"] in failed]
        failures = []

        while entries and retries:
            failures = _delete_batch(entries)
            failures_ids = [rec["Id"] for rec in failures]
            entries = [record for record in entries if record["Id"] in failures_ids]
            retries -= 1

        return {
            "Successful": successful,
            "Failed": failures
        }
