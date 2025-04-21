from aws_cdk import Aws
from aws_cdk import aws_iam as iam
from aws_cdk import aws_eks as eks
from constructs import Construct

def deploy_cluster_autoscaler(scope: Construct, cluster: eks.Cluster):
    sa_name = "cluster-autoscaler"
    sa_ns   = "kube-system"
    autoscaler_sa = cluster.add_service_account(
            "ClusterAutoscalerSA",
            name      = sa_name,
            namespace = sa_ns,
        )

    autoscaler_sa.role.attach_inline_policy(iam.Policy(
        scope, "AutoscalerInlinePolicy",
        document=iam.PolicyDocument(statements=[
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
                resources=["*"]
            )
        ])
    ))

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
