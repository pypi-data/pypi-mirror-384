import requests
from datetime import datetime, timedelta
import pytz

from prefect import get_run_logger

logger = get_run_logger()

def parse_datetime(dt_str):
    """Parse a datetime string into a datetime object."""
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)


def add_version_dependency(versions):
    """
    Finds untagged versions that were created within 2 minutes of any tagged version.

    Args:
    versions (list of dict): List of dictionaries, each containing 'created_at' and possibly 'tags'.

    Returns:
    list: A list of untagged versions that meet the criteria.
    """
    tagged_versions = [v for v in versions if v['metadata']['container']['tags']]
    untagged_versions = [v for v in versions if not v['metadata']['container']['tags']]

    # Convert all creation times to datetime objects
    for v in versions:
        v['created_datetime'] = parse_datetime(v['created_at'])

    # Check each untagged version against all tagged versions
    for v in versions:
        if v in untagged_versions:
            for tagged in tagged_versions:
                time_diff = abs(tagged['created_datetime'] - v['created_datetime'])
                if time_diff < timedelta(minutes=2):
                    v['tag'] = tagged['tag']
                    break  # Stop checking once a close tagged version is found

    return versions


def get_github_package_versions(token, organization, package_type, package_name):
    """
    This function returns all available versions in a github package registry `ghcr`.

    :param: token: GitHub token with proper permissions
    :param: organization: GitHub organization name
    :param: package_type: GitHub package type (e.g. container, npm)
    :param: package_name: GitHub package name
    """
    base_url = f"https://api.github.com/orgs/{organization}/packages/{package_type}/{package_name}/versions"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    versions = []
    url = base_url

    while url:
        logger.info(f"Requesting: {url}")  # Debug output to check the URL being requested
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            page_versions = response.json()
            versions.extend(page_versions)
            link_header = response.headers.get('Link', None)
            if link_header:
                links = {rel.split('; ')[1][5:-1]: rel.split('; ')[0][1:-1] for rel in link_header.split(', ')}
                url = links.get("next", None)  # Get the URL for the next page
                if url:
                    logger.info(f"Next page link found: {url}")  # Debug output to check the next page link
                else:
                    logger.info("No next page link found in header.")  # End of pagination
            else:
                logger.info("No 'Link' header present, likely the last page.")  # If no 'Link' header, it's the last page
                url = None
        else:
            logger.error(f"Failed to retrieve package versions: {response.status_code}, {response.text}")
            url = None
            
    for item in versions:
        tags = item['metadata']['container']['tags']
        item['tag'] = tags[0] if len(tags) > 0 else None
        
    return versions


def delete_versions(versions, token, organization, package_type, package_name):
    """
    :param: versions: list of versions to be deleted
    :param: token: GitHub token with proper permissions
    :param: organization: GitHub organization name
    :param: package_type: GitHub package type (e.g. container, npm)
    :param: package_name: GitHub package name
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    for version in versions:
        delete_url = f"https://api.github.com/orgs/{organization}/packages/{package_type}/{package_name}/versions/{version['id']}"
        response = requests.delete(delete_url, headers=headers)
        if response.status_code == 204:
            logger.info(f"Successfully deleted version: {version['metadata']['container']['tags']} (ID: {version['id']})")
        else:
            logger.info(f"Failed to delete version: {version['metadata']['container']['tags']} (ID: {version['id']}), {response.status_code}, {response.text}")



def delete_untaged_versions(versions, token, organization, package_type, package_name):
    # Identifying untagged versions that are related to a tagged version
    untag_test = list(filter(lambda ver: ver['tag'] is None, versions))
    logger.info(f"UNTAGGED BEFORE: {len(untag_test)}")
    versions   = add_version_dependency(versions)
    untag_vers = list(filter(lambda ver: ver['tag'] is None, versions))
    logger.info(f"UNTAGGED BEFORE: {len(untag_vers)}")
    
    delete_versions(untag_vers, token, organization, package_type, package_name)


def task_get_latest_image_digest(versions, tag_name):
    lst = list(filter(lambda ver: ver['tag'] == tag_name, versions))
    if len(lst) == 0:
        raise ValueError(f"Provided tag: {tag_name} was not found.")
    
    return lst[0]['name']
