#========================================================================
# This class is deprecated. Please refer to aws.py
#========================================================================
import json
import re
import base64
from packaging import version
from datetime            import datetime   , timezone, timedelta
import boto3
from botocore.exceptions import ClientError
from prefect             import get_run_logger
from kube_watch.enums.providers import AwsResources

logger = get_run_logger()

def create_session(aws_creds):
    """Create a boto3 session."""
    session = boto3.Session(
        aws_access_key_id=aws_creds.get('data').get('access_key'),
        aws_secret_access_key=aws_creds.get('data').get('secret_key'),
        aws_session_token=aws_creds.get('data').get('security_token'),  # Using .get() for optional fields
    )
    logger.info("Created AWS Session Successfully!")
    return session

#========================================================================================
# ECR
#========================================================================================
def _prepare_ecr_secret_data(username, password, auth_token, ecr_url):
        key_url = f"https://{ecr_url}"
        docker_config_dict = {
            "auths": {
                key_url: {
                    "username": username,
                    "password": password,
                    "auth": auth_token,
                }
            }
        }
        return {'.dockerconfigjson': json.dumps(docker_config_dict)}

def task_get_access_token(session, resource, region, base_image_url):

    if resource == AwsResources.ECR:
        ecr_client = session.client('ecr', region_name=region)
        token_response = ecr_client.get_authorization_token()
        decoded_token = base64.b64decode(token_response['authorizationData'][0]['authorizationToken']).decode()
        username, password = decoded_token.split(':')
        return _prepare_ecr_secret_data(username, password, token_response['authorizationData'][0]['authorizationToken'], base_image_url)
        # return {'username': username, 'password': password}
    
    raise ValueError('Unknown resource')


def task_get_latest_image_digest(session, resource, region, repository_name, tag):
    """
    Fetches the digest of the latest image from the specified ECR repository.
    """
    if resource == AwsResources.ECR:
        ecr_client = session.client('ecr', region_name=region)
        try:
            response = ecr_client.describe_images(
                repositoryName=repository_name,
                imageIds = [{'imageTag': tag}],
                filter={'tagStatus': 'TAGGED'}
            )
            images = response['imageDetails']
            # Assuming 'latest' tag is used correctly, there should be only one such image
            if images:
                # Extracting the digest of the latest image
                return images[0]['imageDigest']
        except Exception as e:
            logger.error(f"Error fetching latest image digest: {e}")
        return None
    
    raise ValueError('Unknown resource')


def task_get_highest_version_tag(session, resource, region, repository_name, tag_pattern=r"^v?(?P<version>\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?)$"):
    """
    Fetches the highest versioned tag from an ECR repository, similar to FluxCD's semver filter.
    
    Args:
        session: boto3 session
        resource: AwsResources enum
        region: AWS region
        repository_name: Name of the ECR repository
        tag_pattern: Regex pattern to extract version component (default: semver)
    
    Returns:
        The highest matching tag or None if not found.
    """
    if resource == AwsResources.ECR:
        ecr_client = session.client('ecr', region_name=region)
        try:
            pattern = re.compile(tag_pattern)
            paginator = ecr_client.get_paginator('describe_images')
            matched_tags = []

            for page in paginator.paginate(repositoryName=repository_name, filter={'tagStatus': 'TAGGED'}):
                for image in page.get('imageDetails', []):
                    for tag in image.get('imageTags', []):
                        match = pattern.match(tag)
                        if match:
                            ver_str = match.group('version')
                            matched_tags.append((tag, version.parse(ver_str)))

            if not matched_tags:
                logger.info(f"No tags matching pattern '{tag_pattern}' found in repository {repository_name}.")
                return None

            # Sort by semantic version and pick the highest
            highest_tag, _ = max(matched_tags, key=lambda t: t[1])
            return highest_tag

        except Exception as e:
            logger.error(f"Error fetching highest version tag from {repository_name}: {e}")
            return None

    raise ValueError('Unknown resource')

#========================================================================================
# IAM Cred update
#========================================================================================
def task_rotate_iam_creds(
        session,
        user_name,
        old_access_key_id,
        old_access_key_secret,
        access_key_id_var_name,
        access_secret_key_var_name,
        rotate_interval,
        require_smtp_conversion = False,
        ses_region = "ap-southeast-2"
    ):
    iam = session.client('iam')
    creation_date              = None

    # Retrieve the specified access key
    has_key_exist = False
    try:
        response = iam.list_access_keys(UserName=user_name)
        for key in response['AccessKeyMetadata']:
            if key['AccessKeyId'] == old_access_key_id:
                creation_date = key['CreateDate']
                has_key_exist = True
                break
    except ClientError as error:
        logger.error(f"Error retrieving key: {error}")
        raise Exception(f"Error retrieving key: {error}")

    if not has_key_exist:
        logger.error(f"The provided Access Key ID; {old_access_key_id} does not exist.")
        raise  KeyError(f"The provided Access Key ID; {old_access_key_id} does not exist.")

    dd, hh, mm = list(map(lambda x: int(x), rotate_interval.split(":")))
   
    curr_date = datetime.now(timezone.utc)
    # Check if the key needs rotation
    if (curr_date - creation_date > timedelta(days=dd,hours=hh,minutes=mm)):
        logger.info("Key is older than rotation period, rotating now.")
        # Delete the old key
        delete_iam_user_key(session, user_name, old_access_key_id)

        # Create a new access key
        access_key_id, secret_access_key = create_iam_user_key(session, user_name)
        if require_smtp_conversion:
            secret_access_key = convert_to_smtp_password(secret_access_key, ses_region)
        return {access_key_id_var_name: access_key_id, access_secret_key_var_name: secret_access_key}
        
    else:
        logger.info("Key rotation not necessary.")
        return {access_key_id_var_name: old_access_key_id, access_secret_key_var_name: old_access_key_secret}



def create_iam_user_key(session, user_name):
    iam       = session.client('iam')
    # Check if the user exists
    try:
        iam.get_user(UserName=user_name)
        logger.info("User exists, proceeding to create access key.")
    except iam.exceptions.NoSuchEntityException:
        raise Exception(f"User '{user_name}' does not exist, cannot proceed with key creation.")
    except ClientError as error:
        error_code = error.response['Error']['Code']
        if error_code == 'NoSuchEntity':
            raise Exception(f"User '{user_name}' does not exist in AWS IAM.")
        else:
            raise Exception(f"An unexpected error occurred: {error.response['Error']['Message']}")

    # Create access key for this user    
    response          = iam.create_access_key(UserName=user_name)
    access_key_id     = response['AccessKey']['AccessKeyId']
    secret_access_key = response['AccessKey']['SecretAccessKey']

    # print(access_key_id)
    # print(secret_access_key)
    
    return access_key_id, secret_access_key


def delete_iam_user_key(session, user_name, access_key_id):
    iam               = session.client('iam')
    try:
        iam.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
        logger.info(f"Old key {access_key_id} deleted successfully.")
    except Exception as e:
        raise Exception(f"Failed to delete old key: {e}")

    

def convert_to_smtp_password(secret_access_key, region):
    """Convert IAM Secret Key to SMTP Password."""
    import hmac
    import hashlib
    import base64

    SMTP_REGIONS = [
        'us-east-2',       # US East (Ohio)
        'us-east-1',       # US East (N. Virginia)
        'us-west-2',       # US West (Oregon)
        'ap-south-1',      # Asia Pacific (Mumbai)
        'ap-northeast-2',  # Asia Pacific (Seoul)
        'ap-southeast-1',  # Asia Pacific (Singapore)
        'ap-southeast-2',  # Asia Pacific (Sydney)
        'ap-northeast-1',  # Asia Pacific (Tokyo)
        'ca-central-1',    # Canada (Central)
        'eu-central-1',    # Europe (Frankfurt)
        'eu-west-1',       # Europe (Ireland)
        'eu-west-2',       # Europe (London)
        'sa-east-1',       # South America (Sao Paulo)
        'us-gov-west-1',   # AWS GovCloud (US)
    ]

    # These values are required to calculate the signature. Do not change them.
    DATE = "11111111"
    SERVICE = "ses"
    MESSAGE = "SendRawEmail"
    TERMINAL = "aws4_request"
    VERSION = 0x04


    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    if region not in SMTP_REGIONS:
        raise ValueError(f"The {region} Region doesn't have an SMTP endpoint.")

    signature = sign(("AWS4" + secret_access_key).encode('utf-8'), DATE)
    signature = sign(signature, region)
    signature = sign(signature, SERVICE)
    signature = sign(signature, TERMINAL)
    signature = sign(signature, MESSAGE)
    signature_and_version = bytes([VERSION]) + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode('utf-8')