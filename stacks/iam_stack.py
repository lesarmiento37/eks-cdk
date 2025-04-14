from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

class IamStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        env = self.node.try_get_context("environment")

        eks_role = iam.Role(self, "EksMainRole",
            role_name=f"eks-cluster-pizza-{env}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("eks.amazonaws.com"),
                iam.ServicePrincipal("ec2.amazonaws.com")
            )
        )

        managed_policies = [
            "AmazonEKSVPCResourceController",
            "ElasticLoadBalancingFullAccess",
            "AmazonEKSWorkerNodePolicy",
            "AmazonEC2ContainerRegistryReadOnly",
            "AmazonEKS_CNI_Policy",
            "AmazonEKSClusterPolicy",
            "AmazonEC2ContainerRegistryFullAccess",
            "AutoScalingFullAccess"
        ]

        for policy in managed_policies:
            eks_role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy)
            )
from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

class IamStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        env = self.node.try_get_context("environment")

        eks_role = iam.Role(self, "EksMainRole",
            role_name=f"eks-cluster-pizza-{env}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("eks.amazonaws.com"),
                iam.ServicePrincipal("ec2.amazonaws.com")
            )
        )

        managed_policies = [
            "AmazonEKSVPCResourceController",
            "ElasticLoadBalancingFullAccess",
            "AmazonEKSWorkerNodePolicy",
            "AmazonEC2ContainerRegistryReadOnly",
            "AmazonEKS_CNI_Policy",
            "AmazonEKSClusterPolicy",
            "AmazonEC2ContainerRegistryFullAccess",
            "AutoScalingFullAccess"
        ]

        for policy in managed_policies:
            eks_role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(policy)
            )
