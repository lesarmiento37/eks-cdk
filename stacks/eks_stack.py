from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2, aws_eks as eks
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v32 import KubectlV32Layer
from aws_cdk import aws_iam as iam

class EksClusterStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs): 
        super().__init__(scope, id, **kwargs)

        vpc_id = self.node.try_get_context("vpc_id")
        cluster_name = self.node.try_get_context("cluster_name")
        cluster_version = self.node.try_get_context("cluster_version")
        subnets = self.node.try_get_context("private_subnets_ids")
        node_disk = int(self.node.try_get_context("node_disk"))
        node_types = self.node.try_get_context("node_instance_type")
        node_name = self.node.try_get_context("eks_node_name")

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        subnet_objs = [ec2.Subnet.from_subnet_id(self, f"Subnet{i}", subnet_id)
                       for i, subnet_id in enumerate(subnets)]
        
        kubectl_layer = KubectlV32Layer(self, "KubectlLayer")


        cluster = eks.Cluster(self, "EksCluster",
            cluster_name=cluster_name,
            version=eks.KubernetesVersion.of(cluster_version),
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnets=subnet_objs)],
            default_capacity=0,
            kubectl_layer=kubectl_layer
        )

        cluster.add_nodegroup_capacity("DefaultNodeGroup",
            nodegroup_name=node_name,
            instance_types=[ec2.InstanceType(it) for it in node_types],
            desired_size=2,
            min_size=1,
            max_size=3,
            disk_size=node_disk,
            subnets=ec2.SubnetSelection(subnets=subnet_objs),
            labels={"data": self.node.try_get_context("environment")}
        )

        eks.CfnAddon(self, "VpcCniAddon",
            addon_name="vpc-cni",
            cluster_name=cluster.cluster_name
        )

        self.bastion_role = iam.Role(self, "EksBastionRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy")
            ]
        )

        cluster.aws_auth.add_role_mapping(
            self.bastion_role,
            groups=["system:masters"],
            username="eks-bastion"
        )

        CfnOutput(self, "ClusterEndpoint", value=cluster.cluster_endpoint)
        CfnOutput(self, "ClusterCA", value=cluster.cluster_certificate_authority_data)
