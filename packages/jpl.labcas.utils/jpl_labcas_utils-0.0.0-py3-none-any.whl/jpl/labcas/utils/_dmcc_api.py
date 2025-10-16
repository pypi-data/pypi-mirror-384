# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: DMCC API.'''


from .const import DMCC_TOKEN_API, DMCC_IMAGE_EVENTS
import requests


def dmcc_authenticate(client_id: str, client_secret: str) -> str:
    '''Authenticate to the DMCC's token API with a given client ID and secret, returning a
    bearer token.
    '''
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(DMCC_TOKEN_API, data=data, headers=headers)
    response.raise_for_status()
    return response.json().get('access_token')


def get_image_events(protocol_id: int, token: str):
    '''Retrieve all image events from the DMCC's image event API.'''
    headers = {'Authorization': f'Bearer {token}'}
    params = {'protocolId': protocol_id}
    response = requests.get(DMCC_IMAGE_EVENTS, headers=headers, params=params)
    return response.json()['imagingEventRecords']
