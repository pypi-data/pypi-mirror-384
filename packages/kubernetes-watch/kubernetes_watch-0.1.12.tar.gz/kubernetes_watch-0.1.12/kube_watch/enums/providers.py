from enum import Enum

class Providers(str, Enum):
    AWS   = "aws"
    AZURE = "azure"
    GCP   = "gcp"
    VAULT = "vault"


class AwsResources(str, Enum):
    ECR = "ecr" # elastic container registry
    S3  = "s3"
    IAM = "iam" 