# -*- coding: utf-8 -*-

from typing import List

from core_cdc.base import Record
from core_cdc.targets.base import ITarget

from core_aws.services.sns.client import SnsClient
from core_aws.services.sns.client import SnsMessage


class SnsTarget(ITarget):
    """ To send data to a SQS queue """

    client: SnsClient

    def __init__(
        self,
        aws_region: str,
        topic_arn: str,
        batch_size: int = 10,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.aws_region = aws_region
        self.client = SnsClient(region=aws_region, batch_size=batch_size)
        self.topic_arn = topic_arn
        self.execute_ddl = False

    def _save(self, records: List[Record], **kwargs):
        self.client.publish_batch(
            topic_arn=self.topic_arn,
            messages=[
                SnsMessage(
                    Id=f"{rec.table_name}-{x}",
                    Message=rec.to_json(),
                )
                for x, rec in enumerate(records)
            ]
        )
