from aws_cdk import Aws
from aws_cdk import aws_iam as iam
from aws_cdk import aws_eks as eks
from constructs import Construct

def deploy_alb_controller(scope: Construct, cluster: eks.Cluster):
    alb_sa = cluster.add_service_account(
        "aws-load-balancer-controller",
        name="aws-load-balancer-controller",
        namespace="kube-system"
    )

    alb_policy_statement_json = iam.Policy(scope, "ALBControllerPolicy",
        document=iam.PolicyDocument.from_json({
            "Version": "2012-10-17",
            "Statement": [{
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
            }]
        })
    )

    alb_sa.role.attach_inline_policy(alb_policy_statement_json)

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
