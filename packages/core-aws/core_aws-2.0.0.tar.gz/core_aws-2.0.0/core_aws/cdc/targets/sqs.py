# -*- coding: utf-8 -*-

import json
from typing import List, Optional
from uuid import uuid4

from core_cdc.base import Record
from core_cdc.targets.base import ITarget
from core_mixins.utils import get_batches

from core_aws.services.sqs.client import SqsClient


class SqsTarget(ITarget):
    """ To send data to a SQS queue """

    client: SqsClient

    def __init__(self, aws_region: str, queue_name: str, **kwargs) -> None:
        super().__init__(**kwargs)

        self.aws_region = aws_region
        self.queue_url: Optional[str] = None
        self.execute_ddl = False

        self.queue_name = queue_name
        self.client = SqsClient(region=aws_region)

    def init_client(self, **kwargs) -> None:
        self.queue_url = self.client.get_queue_by_name(self.queue_name).url

    def _save(self, records: List[Record], **kwargs):
        if not self.queue_url:
            raise RuntimeError("SQS queue URL not initialized. Call init_client() first.")

        for batch in get_batches([x.to_json() for x in records], 10):
            self.client.send_message_batch(
                queue_url=self.queue_url,
                entries=[
                    {
                        "Id": str(uuid4()),
                        "MessageBody": json.dumps(entry),
                        "DelaySeconds": 0,
                        # "MessageDeduplicationId": "",
                        # "MessageGroupId": ""
                    } for entry in batch
                ]
            )
