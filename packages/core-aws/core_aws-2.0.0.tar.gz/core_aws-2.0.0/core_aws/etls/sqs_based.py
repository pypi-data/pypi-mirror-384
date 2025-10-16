# -*- coding: utf-8 -*-

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core_aws.etls.base import IBaseEtlOnAWS


class IBaseEtlOnAwsSQS(IBaseEtlOnAWS, ABC):
    """
    Base class for ETL processes that retrieve and process
    messages from AWS SQS.

    This class provides a framework for ETL processes that:
      - Poll messages from an SQS queue in batches.
      - Process each message individually.
      - Delete successfully processed messages from the queue.
      - Continue processing until the queue is empty.
      - Handle message processing errors gracefully.

    The workflow:
      1. Retrieve a batch of messages from SQS.
      2. Process each message via `process_message()`.
      3. Track successfully processed messages.
      4. Delete successful messages from the queue.
      5. Repeat until queue is empty.

    Failed messages remain in the queue and will be retried based on the
    queue's visibility timeout and retry policy.

    Example:
        .. code-block:: python

            class MyDataProcessor(IBaseEtlOnAwsSQS):
                def process_message(self, message: Dict) -> None:
                    body = json.loads(message["Body"])
                    # Process the message data
                    self.database.insert(body["data"])

            processor = MyDataProcessor(
                queue_name="my-data-queue",
                aws_region="us-east-1"
            )
            processor.execute()
        ..
    """

    def __init__(self, queue_name: str, **kwargs: Any) -> None:
        """
        Initialize the SQS-based ETL process.

        :param queue_name: Name of the SQS queue to process messages from.
        :param kwargs: Additional arguments passed to parent IBaseEtlOnAWS class.
        """

        super().__init__(**kwargs)
        self.queue_name = queue_name
        self.queue: Optional[Any] = None

    def pre_processing(self, **kwargs: Any) -> None:
        """
        Pre-processing hook to retrieve the SQS queue reference. Fetches the
        queue object from SQS using the configured queue name. Must be
        called before `_execute()`.

        :param kwargs: Additional arguments passed to parent pre_processing.
        :raises Exception: If queue cannot be found or accessed.
        """

        super().pre_processing(**kwargs)
        try:
            self.queue = self.sqs_client.get_queue_by_name(self.queue_name)
            self.info(f"Successfully connected to queue: {self.queue_name}")

        except Exception as error:
            self.error(f"Failed to get queue '{self.queue_name}': {error}")
            raise

    def _execute(self, *args: Any, **kwargs: Any) -> int:
        """
        Retrieve and process messages from the SQS queue in batches. Continuously
        polls the queue for messages, processes each one, and deletes successfully
        processed messages. Continues until the queue is empty.

        :param args: Positional arguments (unused).
        :param kwargs: Additional arguments (e.g., MaxNumberOfMessages, WaitTimeSeconds).
        :return: Total number of successfully processed messages.
        """

        if not self.queue:
            raise RuntimeError("Queue not initialized. Call pre_processing() first.")

        self.info(f"Starting to process messages from queue: `{self.queue_name}`.")
        queue_url = self.queue.url
        batch_count = 0
        total = 0

        while True:
            batch = self.sqs_client.receive_messages(queue_url=queue_url, **kwargs)
            if not batch:
                self.info("No more messages in queue. Processing complete.")
                break

            batch_count += 1
            self.info(f"Fetching batch #{batch_count}...")
            self.info(f"Retrieved {len(batch)} messages in batch #{batch_count}")
            success_entries: List[Dict[str, str]] = []

            for message in batch:
                message_id = message["MessageId"]
                receipt_handle = message["ReceiptHandle"]
                self.info(f"Processing message: {message_id}...")

                # An exception in one message must not stop the execution...
                try:
                    self.process_message(message)

                    success_entries.append({
                        "Id": message_id,
                        "ReceiptHandle": receipt_handle,
                    })

                    self.info(f"Message {message_id} processed successfully.")
                    total += 1

                except Exception as error:
                    error_details = {
                        "MessageId": message_id,
                        "ReceiptHandle": receipt_handle,
                        "Error": str(error),
                        "ErrorType": type(error).__name__
                    }

                    self.error(
                        f"Failed to process message {message_id}"
                        f": {json.dumps(error_details)}"
                    )

            # Deleting successfully processed messages from the queue...
            if success_entries:
                self.info(f"Deleting {len(success_entries)} successfully processed messages...")

                try:
                    res = self.sqs_client.delete_messages(queue_url, success_entries)
                    successful_deletes = len(res.get("Successful", []))
                    failed_deletes = len(res.get("Failed", []))

                    self.info(
                        f"Deletion result: {successful_deletes} succeeded, "
                        f"{failed_deletes} failed."
                    )

                    if failed_deletes > 0:
                        self.error(f"Failed deletions: {json.dumps(res.get('Failed', []))}")

                except Exception as delete_error:
                    self.error(f"Failed to delete messages: {delete_error}")
            else:
                self.info("No messages to delete in this batch.")

        self.info(f"Processing complete. Total messages processed: {total}")
        return total

    @abstractmethod
    def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a single SQS message. This abstract method
        must be implemented by subclasses to define
        the actual message processing logic.

        :param message:
            The SQS message dictionary containing:
              - MessageId: Unique message identifier.
              - ReceiptHandle: Token for deleting the message.
              - Body: The message content (often JSON string).
              - Attributes: Message attributes.
              - MessageAttributes: Custom message attributes.

        :raises Exception:
            Any exception raised will cause the message to remain
            in the queue for retry according to the queue's visibility
            timeout and redrive policy.

        Example:
            .. code-block:: python

                def process_message(self, message: Dict[str, Any]) -> None:
                    # Parse message body
                    body = json.loads(message["Body"])

                    # Extract and validate data
                    data = body["data"]
                    validate(data)

                    # Process the data
                    self.database.insert(data)
                    self.info(f"Processed message: {message['MessageId']}")
            ..
        """
