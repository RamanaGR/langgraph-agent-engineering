# Milvus on EKS — local equivalent: docker-compose milvus standalone
#
# This module documents the production vector search deployment.
# Full Helm install is performed post-Terraform via eks_milvus/helm-values.yaml.

resource "aws_eks_cluster" "milvus" {
  count = var.environment == "prod" ? 1 : 0

  name     = "${var.project_name}-milvus-${var.environment}"
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = "1.29"

  vpc_config {
    subnet_ids = var.private_subnet_ids
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

resource "aws_iam_role" "eks_cluster" {
  count = var.environment == "prod" ? 1 : 0

  name = "${var.project_name}-eks-milvus-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count = var.environment == "prod" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster[0].name
}

resource "aws_eks_node_group" "milvus" {
  count = var.environment == "prod" ? 1 : 0

  cluster_name    = aws_eks_cluster.milvus[0].name
  node_group_name = "milvus-workers"
  node_role_arn   = aws_iam_role.eks_nodes[0].arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }

  instance_types = ["m6i.xlarge"]
}

resource "aws_iam_role" "eks_nodes" {
  count = var.environment == "prod" ? 1 : 0

  name = "${var.project_name}-eks-nodes-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_policy" {
  count = var.environment == "prod" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes[0].name
}
