from aws_cdk import Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class SecurityGroupStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc_id = self.node.try_get_context("vpc_id")
        environment = self.node.try_get_context("environment")
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        sg = ec2.SecurityGroup(self, "EksSG",
            vpc=vpc,
            allow_all_outbound=True,
            security_group_name=f"eks-inbound-cluster-{environment}",
            description="Allow TLS, HTTP, SSH, EKS from VPC"
        )

        for port, desc in [(443, "TLS"), (8080, "EKS"), (80, "HTTP"), (22, "SSH")]:
            sg.add_ingress_rule(ec2.Peer.ipv4("172.0.0.0/8"), ec2.Port.tcp(port), f"{desc} from VPC")

        Tags.of(sg).add("Name", "allow-eks-access")

        self.eks_sg = sg