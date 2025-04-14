from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from aws_cdk import aws_iam as iam

class BastionHostStack(Stack):
    def __init__(self, scope: Construct, id: str, bastion_role: iam.Role, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc_id = self.node.try_get_context("vpc_id")
        ssh_key_name = self.node.try_get_context("ssh_key_name")
        vpc = ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpc_id)
        access_ip = self.node.try_get_context("access_ip")

        bastion_sg = ec2.SecurityGroup(self, "BastionSG",
            vpc=vpc,
            description="Allow SSH access to Bastion",
            allow_all_outbound=True
        )
        bastion_sg.add_ingress_rule(ec2.Peer.ipv4(access_ip), ec2.Port.all_traffic(), "Allow all traffic from IP")

        user_data_script = ec2.UserData.for_linux()
        user_data_script.add_commands(
            "sudo yum update -y",
            "curl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"",
            "echo \"$(cat kubectl.sha256)  kubectl\" | sha256sum --check",
            "sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl",
            "chmod +x kubectl",
            "kubectl version --client --output=yaml"
            "sudo rm -rf /usr/bin/aws",
            "curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o \"awscliv2.zip\"",
            "unzip awscliv2.zip",
            "sudo ./aws/install --update",
            "aws --version",
            "aws eks --region us-east-1 update-kubeconfig --name data-ops-cluster"
            "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
        )


        ec2.Instance(self, "BastionHost",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            security_group=bastion_sg,
            key_pair=ec2.KeyPair.from_key_pair_name(self, "MyKeyPair", ssh_key_name),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )
