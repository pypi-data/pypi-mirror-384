# -*- coding: utf-8 -*-

"""
AWS Simple Notification Service (SNS) client wrapper.

This module provides a high-level interface for interacting with AWS SNS,
including message publishing to topics, batch operations, and SMS delivery.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from core_mixins.utils import get_batches

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException
from core_aws.services.sqs.client import SqsClient


class SnsMessage:
    """
    Represents an SNS message to be published to a topic, phone number, or endpoint.

    This class encapsulates all parameters needed to publish a message via SNS,
    supporting both simple string messages and structured JSON messages for
    multiprotocol delivery.

    Example:
        .. code-block:: python

            # Simple text message
            msg = SnsMessage(Message="Hello, SNS!")

            # Structured message with subject
            msg = SnsMessage(
                Message="Important notification",
                Subject="Alert",
                Id="msg-001"
            )

            # Dict message (auto-converted to JSON)
            msg = SnsMessage(
                Message={"user_id": 123, "event": "signup"},
                Id="msg-002"
            )

            # FIFO topic message
            msg = SnsMessage(
                Message="Order processed",
                MessageGroupId="orders",
                MessageDeduplicationId="order-12345"
            )
        ..
    """

    # noinspection PyPep8Naming
    def __init__(
        self,
        Message: Dict | str,
        Id: Optional[str] = None,
        Subject: Optional[str] = None,
        MessageStructure: Optional[str] = None,
        MessageAttributes: Optional[Dict] = None,
        MessageDeduplicationId: Optional[str] = None,
        MessageGroupId: Optional[str] = None,
    ) -> None:
        """
        Initialize an SNS message.

        :param Message:
            The message content to send. Can be either a string or dict.

            - **String**: Sent as-is to all transport protocols.
            - **Dict**: Automatically converted to JSON structure with "default" key.

            Constraints:
                - Except for SMS: UTF-8 strings, max 256 KB (262,144 bytes).
                - SMS: Max 140-160 characters depending on encoding.
                  Messages longer than limit are split. Total SMS limit: 1,600 characters.

        :param Id:
            Unique identifier for the message within a batch. Required for
            `publish_batch()` operation, ignored for single `publish()` calls.

        :param Subject:
            Optional subject line for email endpoints. Also included in standard
            JSON messages delivered to other endpoints.

        :param MessageStructure:
            Set to "json" to send different messages per protocol.

            When set to "json", the Message parameter must:
              - Be valid JSON
              - Contain at least a "default" key with a string value
              - Optionally contain protocol-specific keys ("http", "sms", "email", etc.)

            Example JSON structure:
                {"default": "Default message", "sms": "Short SMS", "email": "Detailed email"}

        :param MessageAttributes:
            Custom message attributes for filtering and routing. Dict of attribute
            names to attribute values with DataType and StringValue/BinaryValue.

        :param MessageDeduplicationId:
            FIFO topics only. Deduplication token (up to 128 alphanumeric + punctuation).
            Messages with same ID within 5 minutes are treated as duplicates.

            If topic has ContentBasedDeduplication, this overrides auto-generated ID.

        :param MessageGroupId:
            FIFO topics only (required). Message group tag (up to 128 alphanumeric + punctuation).
            Messages in same group are processed in FIFO order. Messages in
            different groups may process out of order.
        """

        self.Id = Id
        self.Message = Message
        self.Subject = Subject

        self.MessageStructure = MessageStructure
        self.MessageAttributes = MessageAttributes
        self.MessageDeduplicationId = MessageDeduplicationId
        self.MessageGroupId = MessageGroupId

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary for SNS API calls. Automatically
        handles dict messages by converting them to JSON structure with "default"
        key. Removes None/empty values.

        :return: Dictionary ready for SNS publish/publish_batch API.

        Example:
            .. code-block:: python

                msg = SnsMessage(Message="Hello", Subject="Test", Id="msg-1")
                payload = msg.as_dict()
                # {"Id": "msg-1", "Message": "Hello", "Subject": "Test"}

                msg2 = SnsMessage(Message={"data": 123})
                payload2 = msg2.as_dict()
                # {
                #   "Message": '{"default": "{\\"data\\": 123}"}',
                #   "MessageStructure": "json"
                # }
            ..
        """

        res = {
            "Id": self.Id,
            "Message": self.Message,
            "Subject": self.Subject,
            "MessageStructure": self.MessageStructure,
            "MessageAttributes": self.MessageAttributes,
            "MessageDeduplicationId": self.MessageDeduplicationId,
            "MessageGroupId": self.MessageGroupId
        }

        # Converting dict messages to JSON structure...
        if isinstance(self.Message, dict):
            res["MessageStructure"] = "json"
            res["Message"] = json.dumps({"default": json.dumps(self.Message)})

        # Removing None/empty values...
        for key, value in list(res.items()):
            if not value:
                del res[key]

        return res


class SnsClient(AwsClient):
    """
    Client for AWS Simple Notification Service (SNS). This client
    provides methods for publishing messages to SNS topics, endpoints,
    and phone numbers. Supports both single and batch operations.

    Example:
        .. code-block:: python

            # Initialize client
            sns = SnsClient(region="us-east-1")

            # Publish to topic
            msg = SnsMessage(Message="Hello, SNS!", Subject="Notification")
            sns.publish_message(msg, topic_arn="arn:aws:sns:us-east-1:123:my-topic")

            # Publish multiple messages
            messages = [
                SnsMessage(Message="Message 1", Id="msg-1"),
                SnsMessage(Message="Message 2", Id="msg-2")
            ]
            sns.publish_batch("arn:aws:sns:us-east-1:123:my-topic", messages)
        ..
    """

    client: "mypy_boto3_sns.client.SNSClient"  # type: ignore[name-defined]
    resource: Any  # boto3.resources.factory.sns.ServiceResource
    batch_size: int

    def __init__(
        self,
        region: str,
        batch_size: int = 10,
        **kwargs: Any
    ) -> None:
        """
        Initialize the SNS client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param batch_size: Maximum messages per batch (default: 10, max: 10).
        :param kwargs: Additional arguments passed to boto3.client().
        """

        super().__init__("sns", region_name=region, **kwargs)
        self.resource = boto3.resource("sns", region_name=region, **kwargs)
        self.batch_size = batch_size

    def create_topic(
        self,
        name: str,
        attributes: Optional[Dict[str, str]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        data_protection_policy: Optional[str] = None,
    ) -> str:
        """
        Create a new SNS topic. Creates a standard or FIFO topic based on name
        suffix (.fifo for FIFO topics). Returns the topic ARN for publishing messages
        and subscribing endpoints.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/create_topic.html

        :param name:
            Topic name. Must be 1-256 characters, alphanumeric plus hyphens and
            underscores. For FIFO topics, name must end with ".fifo" suffix.

        :param attributes:
            Optional topic configuration attributes. Common attributes:

            - **DeliveryPolicy**: JSON string for delivery retry policy
            - **DisplayName**: Human-readable name for SMS sender (max 100 chars)
            - **FifoTopic**: "true" for FIFO topic (auto-set if name ends with .fifo)
            - **ContentBasedDeduplication**: "true" to enable content-based deduplication (FIFO only)
            - **KmsMasterKeyId**: AWS KMS key ID for encryption
            - **Policy**: JSON string for topic access policy

        :param tags:
            Optional list of tags to apply to the topic. Each tag is a dict with
            'Key' and 'Value' fields. Maximum 50 tags per topic.

            Example: [{"Key": "Environment", "Value": "Production"}]

        :param data_protection_policy:
            Optional JSON string defining data protection policy for sensitive
            data scanning and redaction.

        :return: The ARN (Amazon Resource Name) of the created topic.

        :raises AwsClientException: If topic creation fails.

        Example:
            .. code-block:: python

                sns = SnsClient(region="us-east-1")

                # Create standard topic
                topic_arn = sns.create_topic(name="my-notifications")
                print(f"Created topic: {topic_arn}")

                # Create FIFO topic with attributes
                fifo_arn = sns.create_topic(
                    name="my-orders.fifo",
                    attributes={
                        "FifoTopic": "true",
                        "ContentBasedDeduplication": "true"
                    },
                    tags=[
                        {"Key": "Environment", "Value": "Production"},
                        {"Key": "Application", "Value": "OrderProcessing"}
                    ]
                )

                # Create topic with KMS encryption
                encrypted_arn = sns.create_topic(
                    name="secure-topic",
                    attributes={
                        "KmsMasterKeyId": "alias/aws/sns",
                        "DisplayName": "Secure Notifications"
                    }
                )
            ..

        Note:
          - Topic names are case-sensitive
          - Creating a topic with existing name is idempotent (returns existing ARN)
          - FIFO topics support message ordering and deduplication
          - Standard topics offer best-effort ordering and at-least-once delivery
        """

        kwargs: Dict[str, Any] = {"Name": name}

        if attributes:
            kwargs["Attributes"] = attributes

        if tags:
            kwargs["Tags"] = tags

        if data_protection_policy:
            kwargs["DataProtectionPolicy"] = data_protection_policy

        try:
            response = self.client.create_topic(**kwargs)
            return response["TopicArn"]

        except ClientError as error:
            raise AwsClientException(error) from error

    def subscribe_sqs_queue(
        self,
        topic_arn: str,
        queue_name: str,
        region: Optional[str] = None,
        set_queue_policy: bool = True,
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Subscribe an SQS queue to an SNS topic by queue name. This is a convenience
        method that handles the entire subscription process, including setting up
        the necessary queue policy to allow SNS to send messages.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/subscribe.html

        :param topic_arn:
            ARN of the SNS topic to subscribe the queue to.

        :param queue_name:
            Name of the SQS queue to subscribe. The queue must exist in the same
            region as the SNS client or in the specified region.

        :param region:
            Optional AWS region where the SQS queue exists. If not specified,
            uses the same region as the SNS client.

        :param set_queue_policy:
            If True (default), automatically sets the SQS queue policy to allow
            the SNS topic to send messages. Set to False if you want to manage
            the queue policy manually.

        :param attributes:
            Optional subscription attributes. Common attributes:

            - **RawMessageDelivery**: "true" to deliver raw messages without SNS envelope (default: "false")
            - **FilterPolicy**: JSON string for message filtering based on attributes
            - **RedrivePolicy**: JSON string defining dead-letter queue for failed deliveries

        :return: The subscription ARN for the created subscription.

        :raises AwsClientException: If subscription fails or queue doesn't exist.

        Example:
            .. code-block:: python

                from core_aws.services.sns.client import SnsClient
                from core_aws.services.sqs.client import SqsClient

                sns = SnsClient(region="us-east-1")
                sqs = SqsClient(region="us-east-1")

                # Create topic and queue
                topic_arn = sns.create_topic(name="notifications")
                queue_url = sqs.create_queue(queue_name="notification-queue")

                # Subscribe queue to topic (automatically sets queue policy)
                subscription_arn = sns.subscribe_sqs_queue(
                    topic_arn=topic_arn,
                    queue_name="notification-queue"
                )

                print(f"Subscribed: {subscription_arn}")

                # Subscribe with raw message delivery
                subscription_arn = sns.subscribe_sqs_queue(
                    topic_arn=topic_arn,
                    queue_name="notification-queue",
                    attributes={
                        "RawMessageDelivery": "true"
                    }
                )

                # Subscribe with message filtering
                subscription_arn = sns.subscribe_sqs_queue(
                    topic_arn=topic_arn,
                    queue_name="notification-queue",
                    attributes={
                        "FilterPolicy": json.dumps({
                            "event_type": ["order_placed", "order_shipped"]
                        })
                    }
                )
            ..

        Note:
          - The SQS queue must exist before calling this method
          - By default, sets queue policy to allow SNS to send messages
          - Subscription is confirmed automatically for SQS endpoints
          - For cross-region subscriptions, specify the queue's region
        """

        try:
            # Initialize SQS client in the appropriate region
            queue_region = region or self.client.meta.region_name
            sqs_client = SqsClient(region=queue_region)

            # Get queue attributes to retrieve ARN
            queue = sqs_client.get_queue_by_name(queue_name)
            queue_arn = queue.attributes.get("QueueArn")
            queue_url = queue.url

            if not queue_arn:
                raise AwsClientException(
                    f"Could not retrieve ARN for queue: {queue_name}!"
                )

            # Set queue policy to allow SNS to send messages (if requested)
            if set_queue_policy:
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "sns.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": queue_arn,
                        "Condition": {
                            "ArnEquals": {"aws:SourceArn": topic_arn}
                        }
                    }]
                }

                sqs_client.client.set_queue_attributes(
                    QueueUrl=queue_url,
                    Attributes={"Policy": json.dumps(policy)}
                )

            # Subscribe the queue to the topic
            subscribe_kwargs: Dict[str, Any] = {
                "TopicArn": topic_arn,
                "Protocol": "sqs",
                "Endpoint": queue_arn
            }

            if attributes:
                subscribe_kwargs["Attributes"] = attributes

            response = self.client.subscribe(**subscribe_kwargs)
            return response["SubscriptionArn"]

        except ClientError as error:
            raise AwsClientException(error) from error

    def publish_message(
        self,
        message: SnsMessage,
        topic_arn: Optional[str] = None,
        target_arn: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish a message to an SNS topic, mobile endpoint, or phone
        number. Sends a message to one of three destinations: an SNS topic (fan-out),
        a mobile platform endpoint (push notification), or a phone number (SMS).
        Exactly one destination must be specified.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/publish.html

        :param message: SnsMessage object containing the message and metadata.

        :param topic_arn:
            ARN of the SNS topic to publish to. Required if target_arn and
            phone_number are not specified.

        :param target_arn:
            ARN of mobile platform endpoint or device. Required if topic_arn
            and phone_number are not specified.

        :param phone_number:
            Phone number in E.164 format (e.g., +14155551234). Required if
            topic_arn and target_arn are not specified.

        :return:
            Dictionary containing:
              - **MessageId** (str): Unique identifier for the published message.
              - **SequenceNumber** (str, optional): For FIFO topics only.

        :raises AwsClientException:
            If no destination specified or if publishing fails.

        Example:
            .. code-block:: python

                sns = SnsClient(region="us-east-1")

                # Publish to topic
                msg = SnsMessage(Message="Hello!", Subject="Notification")
                response = sns.publish_message(
                    msg,
                    topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic"
                )
                print(f"Published: {response['MessageId']}")

                # Send SMS
                sms_msg = SnsMessage(Message="Your code is: 123456")
                sns.publish_message(sms_msg, phone_number="+14155551234")

                # Publish to mobile endpoint
                push_msg = SnsMessage(Message="New message!")
                sns.publish_message(
                    push_msg,
                    target_arn="arn:aws:sns:us-east-1:123:endpoint/APNS/MyApp/abc123"
                )
            ..
        """

        if not any([topic_arn, target_arn, phone_number]):
            raise AwsClientException(
                "You must specify one of: topic_arn, target_arn, or phone_number"
            )

        message.Id = None
        kwargs = message.as_dict()

        for key, value in (("TargetArn", target_arn), ("TopicArn", topic_arn), ("PhoneNumber", phone_number)):
            if value:
                kwargs[key] = value

        try:
            return self.client.publish(**kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def publish_batch(
        self,
        topic_arn: str,
        messages: List[SnsMessage]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Publish multiple messages to an SNS topic in batches. Publishes up
        to 10 messages per API call. For FIFO topics, messages within a batch
        are published in order and deduplicated within/across batches for 5
        minutes. Automatically handles larger message lists
        by batching into chunks of `batch_size`.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/publish_batch.html

        :param topic_arn: ARN of the SNS topic to publish to.

        :param messages:
            List of SnsMessage objects to publish. Each message must have
            a unique `Id` field within the batch.

        :return:
            Dictionary containing aggregated results from all batches:

            .. code-block:: python

                {
                    "Successful": [
                        {
                            "Id": "string",
                            "MessageId": "string",
                            "SequenceNumber": "string"  # FIFO only
                        }
                    ],
                    "Failed": [
                        {
                            "Id": "string",
                            "Code": "string",
                            "Message": "string",
                            "SenderFault": True | False
                        }
                    ]
                }
            ..

        :raises AwsClientException: If batch publishing fails.

        Example:
            .. code-block:: python

                sns = SnsClient(region="us-east-1")

                # Create messages with unique IDs
                messages = [
                    SnsMessage(Message="First message", Id="msg-1"),
                    SnsMessage(Message="Second message", Id="msg-2"),
                    SnsMessage(Message="Third message", Id="msg-3")
                ]

                # Publish batch
                result = sns.publish_batch(
                    topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
                    messages=messages
                )

                print(f"Successful: {len(result['Successful'])}")
                print(f"Failed: {len(result['Failed'])}")

                # Check failures
                for failure in result.get('Failed', []):
                    print(f"Failed {failure['Id']}: {failure['Message']}")
            ..

        Note:
          - Each message must have a unique `Id` field
          - Max 10 messages per batch (enforced by batch_size)
          - For FIFO topics, MessageGroupId is required
          - Total payload size per batch must be < 256 KB
        """

        result = defaultdict(list)

        try:
            for batch in get_batches(messages, self.batch_size):
                response = self.client.publish_batch(
                    TopicArn=topic_arn,
                    PublishBatchRequestEntries=[x.as_dict() for x in batch])

                for key, value in response.items():
                    result[key].extend(value)

            return dict(result)

        except ClientError as error:
            raise AwsClientException(error) from error
