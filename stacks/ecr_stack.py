from aws_cdk import Stack
from aws_cdk import aws_ecr as ecr
from constructs import Construct

class EcrStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        ecr_name = self.node.try_get_context("ecr_name")

        ecr.Repository(self, "DataOpsRepo",
            repository_name=ecr_name,
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.MUTABLE
        )
