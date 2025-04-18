from aws_cdk import Stack, CfnOutput, Aws, CfnJson
from aws_cdk import aws_ec2 as ec2, aws_eks as eks
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v32 import KubectlV32Layer
from aws_cdk import aws_iam as iam
from aws_cdk import Tags
from aws_cdk import custom_resources as cr

class EksClusterStack(Stack):
    def __init__(self, scope: Construct, id: str, control_plane_sg: ec2.SecurityGroup, **kwargs): 
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
            security_group=control_plane_sg,
            kubectl_layer=kubectl_layer
        )

        nodegroup = cluster.add_nodegroup_capacity("DefaultNodeGroup",
            nodegroup_name=node_name,
            instance_types=[ec2.InstanceType(it) for it in node_types],
            desired_size=2,
            min_size=1,
            max_size=3,
            disk_size=node_disk,
            subnets=ec2.SubnetSelection(subnets=subnet_objs),
            labels={"data": self.node.try_get_context("environment")}
        )

        nodegroup.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:SetDesiredCapacity",
                    "autoscaling:TerminateInstanceInAutoScalingGroup",
                ],
                resources=["*"],
            )
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

        cluster.open_id_connect_provider

        alb_policy_statement_json = iam.PolicyDocument.from_json({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "elasticloadbalancing:*",
                        "ec2:Describe*",
                        "ec2:CreateSecurityGroup",
                        "ec2:CreateTags",
                        "ec2:AuthorizeSecurityGroupIngress",
                        "ec2:RevokeSecurityGroupIngress",
                        "ec2:DeleteSecurityGroup",
                        "iam:CreateServiceLinkedRole",
                        "cognito-idp:DescribeUserPoolClient"
                    ],
                    "Resource": "*"
                }
            ]
        })

        # Create IAM Role with the Policy
        alb_sa = cluster.add_service_account("aws-load-balancer-controller",
            name="aws-load-balancer-controller",
            namespace="kube-system"
        )

        alb_sa.role.attach_inline_policy(iam.Policy(self, "ALBControllerPolicy", document=alb_policy_statement_json))

        # Deploy Helm chart
        cluster.add_helm_chart(
            "AWSLoadBalancerController",
            chart="aws-load-balancer-controller",
            repository="https://aws.github.io/eks-charts",
            namespace="kube-system",
            values={
                "clusterName": cluster.cluster_name,
                "region": Aws.REGION,
                "vpcId": cluster.vpc.vpc_id,
                "serviceAccount": {
                    "create": False,
                    "name": "aws-load-balancer-controller"
                },
                "replicaCount": 1
            }
        )

        for i, subnet_id in enumerate(subnets):
            cr.AwsCustomResource(self, f"TagSubnet{i}",
                on_create=cr.AwsSdkCall(
                    service="EC2",
                    action="createTags",
                    parameters={
                        "Resources": [subnet_id],
                        "Tags": [
                            {"Key": "kubernetes.io/role/elb", "Value": "1"},
                            {"Key": f"kubernetes.io/cluster/{cluster_name}", "Value": "shared"}
                        ]
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"TagSubnet{i}")
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                    resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                )
            )

        # ────────────  Cluster Autoscaler  ────────────

        sa_name = "cluster-autoscaler"
        sa_ns   = "kube-system"

        # 1) ServiceAccount + IAM role (CDK hace todo por ti)
        autoscaler_sa = cluster.add_service_account(
            "ClusterAutoscalerSA",
            name      = sa_name,
            namespace = sa_ns,
        )

        autoscaler_sa.role.attach_inline_policy(
            iam.Policy(
                self, "AutoscalerInlinePolicy",
                document=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "autoscaling:DescribeAutoScalingGroups",
                                "autoscaling:DescribeAutoScalingInstances",
                                "autoscaling:DescribeLaunchConfigurations",
                                "autoscaling:DescribeTags",
                                "autoscaling:SetDesiredCapacity",
                                "autoscaling:TerminateInstanceInAutoScalingGroup",
                                "ec2:DescribeLaunchTemplateVersions",
                                "ec2:DescribeInstanceTypes",
                                "ec2:DescribeInstances",
                                "sts:*"
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            )
        )

        cluster.add_helm_chart(
            "ClusterAutoscaler",
            chart      = "cluster-autoscaler",
            repository = "https://kubernetes.github.io/autoscaler",
            release    = "cluster-autoscaler",
            namespace  = sa_ns,
            values = {
                "autoDiscovery": {"clusterName": cluster.cluster_name},
                "awsRegion": Aws.REGION,
                "serviceAccount": {
                    "create": False,         
                    "name": sa_name,
                },
                "extraArgs": {
                    "balance-similar-node-groups": "true",
                    "skip-nodes-with-local-storage": "false",
                    "scan-interval": "10s",
                },
            },
        )
        # -------------------------------------------------------




        CfnOutput(self, "ClusterEndpoint", value=cluster.cluster_endpoint)
        CfnOutput(self, "ClusterCA", value=cluster.cluster_certificate_authority_data)
