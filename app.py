#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_cdk import App, Environment
from aws_cdk import aws_iam as iam
from stacks.eks_stack import EksClusterStack
from stacks.iam_stack import IamStack
from stacks.ecr_stack import EcrStack
from stacks.sg_stack import SecurityGroupStack
from stacks.bastion_stack import BastionHostStack

app = cdk.App()

account = app.node.try_get_context("account")
region = app.node.try_get_context("region")

env = cdk.Environment(account=account, region=region)

sg_stack = SecurityGroupStack(app, "SGStack", env=env)
iam_stack = IamStack(app, "IAMStack", env=env)
ecr_stack = EcrStack(app, "ECRStack", env=env)
eks_stack = EksClusterStack(app, "EksClusterStack", control_plane_sg=sg_stack.eks_sg, env=env)

bastion_stack = BastionHostStack(
    app,
    "BastionHostStack",
    bastion_role=eks_stack.bastion_role,
    env=env
)

bastion_stack.add_dependency(eks_stack)



app.synth()

#cdk bootstrap aws://975049963324/us-east-1

