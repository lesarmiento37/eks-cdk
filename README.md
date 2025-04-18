# eks-cdk
POC Of  EKS with CDK

aws ec2 create-tags \
  --resources subnet-abc123 subnet-def456 \
  --tags Key=kubernetes.io/role/elb,Value=1

aws ec2 create-tags \
  --resources subnet-abc123 subnet-def456 \
  --tags Key=kubernetes.io/cluster/data-ops-cluster,Value=shared
