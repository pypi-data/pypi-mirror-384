import requests
# from pathlib import Path
import os
import sys

"""
A simple script to:
    1. Retrieve all public records from a CKAN service
    2. Insert CKAN records into a Geonetwork service

This requires the 'iso19115' extension to be installed in CKAN and the following env. vars:
    1. 'CKAN2GN_GN_USERNAME' geonetwork username for an account that can create records
    2. 'CKAN2GN_GN_PASSWORD' geonetwork password for an account that can create records
    3. 'CKAN2GN_GN_URL' geonetork service URL
    4. 'CKAN2GN_CKAN_URL' CKAN service URL
"""

# Geonetwork username and password:
GN_USERNAME = os.environ.get('CKAN2GN_GN_USERNAME')
GN_PASSWORD = os.environ.get('CKAN2GN_GN_PASSWORD')

# Geonetwork and CKAN server URLs
GN_URL = os.environ.get('CKAN2GN_GN_URL')
CKAN_URL = os.environ.get('CKAN2GN_CKAN_URL')

def get_gn_xsrf_token(session):
    """ Retrieves XSRF token from Geonetwork

    :param session: requests Session object
    :returns: XSRF as string or None upon error
    """
    authenticate_url = GN_URL + '/geonetwork/srv/eng/info?type=me'
    response = session.post(authenticate_url)

    # Extract XRSF token
    xsrf_token = response.cookies.get("XSRF-TOKEN")
    if xsrf_token:
        return xsrf_token
    return None

def list_ckan_records():
    """ Contacts CKAN and retrieves a list of package ids for all public records

    :returns: list of package id strings or None upon error
    """
    session = requests.Session()
    url_path =  'api/3/action/package_list' # Path('api') / '3' / 'action' / 'package_list'
    url = f'{CKAN_URL}/{url_path}'
    r = session.get(url)
    resp = r.json()
    if resp['success'] is False:
        return None
    return resp['result']

def get_ckan_record(package_id):
    """ Given a package id retrieves its record metadata

    :param package_id: CKAN package_id string
    :returns: package metadata as a dict or None upon error
    """
    session = requests.Session()
    # Set up CKAN URL
    url_path =  'api/3/action/iso19115_package_show' #  Path('api') / '3' / 'action' / 'iso19115_package_show'
    url = f'{CKAN_URL}/{url_path}'
    r = session.get(url, params={'format':'xml', 'id':package_id})
    resp = r.json()
    if resp['success'] is False:
        return None
    return resp['result']
    

def insert_gn_record(session, xsrf_token, xml_string):
    """ Inserts a record into Geonetwork

    :param session: requests Session object
    :param xsrf_token: Geonetwork's XSRF token as a string
    :param xml_string: XML to be inserted as a string
    :returns: True or False if insert succeeded
    """
    # Set header for connection
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/xml',
               'X-XSRF-TOKEN': xsrf_token
    }

    # Set the parameters
    # Currently 'uuidProcessing' is set to 'NOTHING' so that records that
    # already exist are rejected by Geonetwork as duplicates
    params = {'metadataType': 'METADATA',
              'publishToAll': 'true',
              'uuidProcessing': 'NOTHING',  # Available values : GENERATEUUID, NOTHING, OVERWRITE
    }

    # Send a put request to the endpoint to create record
    response = session.put(GN_URL + '/geonetwork/srv/api/0.1/records',
                        data=xml_string,
                        params=params,
                        auth=(GN_USERNAME, GN_PASSWORD),
                        headers=headers
    )
    resp = response.json()

    # Check if record was created in Geonetwork
    if response.status_code == requests.codes['created'] and resp['numberOfRecordsProcessed'] == 1 and \
            resp['numberOfRecordsWithErrors'] == 0:
        print("Inserted")
        return True
    print(f"Insert failed: status code: {response.status_code}\n{resp}")
    return False
        

if __name__ == "__main__":
    # Check env. vars
    if GN_USERNAME is None or GN_PASSWORD is None or GN_URL is None or CKAN_URL is None:
        print("Please define the following env. vars:")
        print("           'CKAN2GN_GN_USERNAME' 'CKAN2GN_GN_PASSWORD' 'CKAN2GN_GN_URL' 'CKAN2GN_CKAN_URL'")
        sys.exit(1)
    # Connect to server
    session = requests.Session()
    xsrf = get_gn_xsrf_token(session)
    if xsrf is not None:
        # Get records from CKAN
        for id in list_ckan_records():
            print(f"Inserting '{id}'")
            xml_string = get_ckan_record(id)
            if xml_string is not None:
                # Insert GN record
                insert_gn_record(session, xsrf, xml_string)
            else:
                print(f"Could not get record id {id} from CKAN")

    
