#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from stacks.eks_stack import EksClusterStack
from stacks.iam_stack import IamStack
from stacks.ecr_stack import EcrStack
from stacks.sg_stack import SecurityGroupStack
from stacks.bastion_stack import BastionHostStack

app = cdk.App()

region = app.node.try_get_context("region")
account = app.node.try_get_context("account")
env = cdk.Environment(account=account, region=region)

sg_stack = SecurityGroupStack(app, "SGStack", env=env)
iam_stack = IamStack(app, "IAMStack", env=env)
ecr_stack = EcrStack(app, "ECRStack", env=env)
eks_stack = EksClusterStack(app, "EksClusterStack", env=env)
bastion_stack = BastionHostStack(app, "BastionHostStack", env=env, bastion_role=eks_stack.bastion_role)
bastion_stack.add_dependency(eks_stack)
app.synth()

#cdk bootstrap aws://668578428335/us-west-2
#cdk bootstrap aws://381492193208/us-east-1

