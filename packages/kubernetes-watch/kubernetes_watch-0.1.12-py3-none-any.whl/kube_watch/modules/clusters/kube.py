from prefect import get_run_logger
from typing import List
from kubernetes import config, client, utils
from kubernetes.client.rest import ApiException
import base64
import datetime

from kube_watch.enums.kube import Hosts

logger = get_run_logger()

    
def setup(host=Hosts.REMOTE, context=None):
    if host == Hosts.LOCAL:
        # Running outside a Kubernetes cluster (e.g., local development)
        config.load_kube_config(context=context)  # You can specify the context here if necessary   
    else:
        # Running inside a Kubernetes cluster
        config.load_incluster_config()



def create_or_update_configmap(config_name, namespace, data):
    """
    Create or update a ConfigMap in a specified namespace if the data is different.
    
    :param config_name: The name of the ConfigMap.
    :param namespace: The namespace of the ConfigMap.
    :param data: A dictionary containing the data for the ConfigMap.
    :return: True if the ConfigMap was created or updated, False otherwise.
    """
    v1 = client.CoreV1Api()
    configmap_metadata = client.V1ObjectMeta(name=config_name, namespace=namespace)
    configmap = client.V1ConfigMap(api_version="v1", kind="ConfigMap", metadata=configmap_metadata, data=data)
    
    try:
        existing_configmap = v1.read_namespaced_config_map(name=config_name, namespace=namespace)
        # Compare the existing ConfigMap's data with the new data
        if existing_configmap.data == data:
            logger.info("No update needed for ConfigMap: {}".format(config_name))
            return False
        else:
            # Data is different, update the ConfigMap
            api_response = v1.replace_namespaced_config_map(name=config_name, namespace=namespace, body=configmap)
            logger.info("ConfigMap updated. Name: {}".format(api_response.metadata.name))
            return True
    except ApiException as e:
        if e.status == 404:  # ConfigMap not found, create it
            try:
                api_response = v1.create_namespaced_config_map(namespace=namespace, body=configmap)
                logger.info("ConfigMap created. Name: {}".format(api_response.metadata.name))
                return {'trigger_restart': True}
            except ApiException as e:
                logger.error("Exception when creating ConfigMap: {}".format(e))
                raise ValueError
        else:
            logger.error("Failed to get or create ConfigMap: {}".format(e))
            raise ValueError
        

def create_or_update_secret(secret_name, namespace, data, secret_type = None):
    """
    Create or update a Secret in a specified namespace if the data is different.
    
    :param name: The name of the Secret.
    :param namespace: The namespace of the Secret.
    :param data: A dictionary containing the data for the Secret. Values must be strings (not Base64 encoded).
    :return: True if the secret was created or updated, False otherwise.
    """
    if secret_type == None:
        secret_type = "Opaque"

    v1 = client.CoreV1Api()
    secret_metadata = client.V1ObjectMeta(name=secret_name, namespace=namespace)
    secret = client.V1Secret(
        api_version="v1", 
        kind="Secret", 
        metadata=secret_metadata, 
        string_data=data,
        type=secret_type
    )
    
    try:
        existing_secret = v1.read_namespaced_secret(name=secret_name, namespace=namespace)
        # Encode the new data to compare with the existing Secret
        encoded_data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
        
        # Check if the existing secret's data matches the new data
        if existing_secret.data == encoded_data:
            logger.info("No update needed for Secret: {}".format(secret_name))
            return False
        else:
            # Data is different, update the Secret
            api_response = v1.replace_namespaced_secret(name=secret_name, namespace=namespace, body=secret)
            logger.info("Secret updated. Name: {}".format(api_response.metadata.name))
            return True

    except ApiException as e:
        if e.status == 404:  # Secret not found, create it
            try:
                api_response = v1.create_namespaced_secret(namespace=namespace, body=secret)
                logger.info("Secret created. Name: {}".format(api_response.metadata.name))
                return {'trigger_restart':  True}
            except ApiException as e:
                logger.error("Exception when creating Secret: {}".format(e))
                raise ValueError
        else:
            logger.error("Failed to get or create Secret: {}".format(e))
            raise ValueError
        

def get_kubernetes_secret(secret_name, namespace):
    # Assuming that the Kubernetes configuration is already set
    v1 = client.CoreV1Api()
    try:
        secret = v1.read_namespaced_secret(secret_name, namespace)
        # Decoding the base64 encoded data
        decoded_data = {key: base64.b64decode(value).decode('utf-8') for key, value in secret.data.items()}
        return decoded_data
    except ApiException as e:
        logger.error(f"Failed to get secret: {e}")
        return None
    

def restart_deployment(deployment, namespace):
    """
    Trigger a rollout restart of a deployment in a specified namespace.

    :param name: The name of the deployment.
    :param namespace: The namespace of the deployment.
    """ 

    v1 = client.AppsV1Api()
    body = {
        'spec': {
            'template': {
                'metadata': {
                    'annotations': {
                        'kubectl.kubernetes.io/restartedAt': datetime.datetime.utcnow().isoformat()
                    }
                }
            }
        }
    }
    try:
        api_response = v1.patch_namespaced_deployment(name=deployment, namespace=namespace, body=body)
        logger.info(f"Deployment restarted. Name: {api_response.metadata.name}")
    except ApiException as e:
        logger.error(f"Exception when restarting deployment: {e}")


def has_mismatch_image_digest(repo_digest, label_selector, namespace):
    """
    Check all pods in the given namespace and matching the label selector for any
    mismatch between the latest image digest and the current image digest.
    
    parameters:
    - namespace: The namespace to search for pods.
    - label_selector: The label selector to identify the relevant pods.
    - repo_digest: The latest image digest to compare against.
    
    Returns:
    - True if any pod is found with an image digest mismatch.
    - False if all pods match the latest image digest.
    """
    core_v1_api         = client.CoreV1Api()

    # Fetch pods based on namespace and label selector
    pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
    
    # Iterate over pods and their containers
    for pod in pods.items:
        for container_status in pod.status.container_statuses:
            current_image_id = container_status.image_id
            # Check for digest mismatch
            if current_image_id.split('@')[-1] != repo_digest:
                logger.info(f"Mismatch found in pod: {pod.metadata.name}, container: {container_status.name}")
                logger.info(f"Repo digest: {repo_digest}")
                logger.info(f"Curr digest: {current_image_id.split('@')[-1]}")
                return True
    
    logger.info("Images are in-sync.")
    logger.info(f"Repo digest: {repo_digest}")
    logger.info(f"Curr digest: {current_image_id.split('@')[-1]}")
    return False


def update_deployment_image_if_needed(namespace, deployment_name, container_name, new_tag):
    """
    Updates the deployment's container image tag only if it differs from the current one.
    The repository URI is extracted automatically from the current image reference.

    Args:
        namespace: Kubernetes namespace where the deployment resides.
        deployment_name: Name of the deployment to patch.
        container_name: Name of the container inside the deployment.
        new_tag: The new image tag to set, e.g. 'v1.2.3'

    Returns:
        True if the image was updated and rollout triggered, False otherwise.
    """
    try:
        # Load kube config (works both in-cluster and local)
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        apps_v1 = client.AppsV1Api()

        # Read the current deployment
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)

        # Find the container we want to update
        containers = deployment.spec.template.spec.containers
        target_container = next((c for c in containers if c.name == container_name), None)
        if not target_container:
            logger.error(f"Container '{container_name}' not found in deployment '{deployment_name}'.")
            return False

        current_image = target_container.image
        if ':' in current_image:
            repo_uri, current_tag = current_image.rsplit(':', 1)
        else:
            repo_uri, current_tag = current_image, "latest"

        if current_tag == new_tag:
            logger.info(f"No update needed. Deployment '{deployment_name}' already using tag '{new_tag}'.")
            return False

        # Build the new image reference using same repo
        new_image = f"{repo_uri}:{new_tag}"
        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {"name": container_name, "image": new_image}
                        ]
                    }
                }
            }
        }

        logger.info(f"Updating '{deployment_name}' from '{current_image}' to '{new_image}'")
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=patch
        )

        logger.info(f"Deployment '{deployment_name}' successfully updated to {new_image}")
        return True

    except Exception as e:
        logger.error(f"Failed to update deployment '{deployment_name}': {e}")
        return False