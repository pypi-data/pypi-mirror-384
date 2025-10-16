import requests
from requests.auth import HTTPBasicAuth
from mendeley import Mendeley
from mendeley.session import MendeleySession


API_URL = 'https://api.mendeley.com/oauth/token'


def get_session(client_id: str, client_secret: str):
    mendeley = Mendeley(client_id=client_id, client_secret=client_secret)
    auth = mendeley.start_client_credentials_flow()
    try:
        return auth.authenticate()
    except KeyError as e:
        print('an error occured while authenticating', str(e))
        # expired token error, refresh manually
        token = requests.post(API_URL, auth=HTTPBasicAuth(client_id, client_secret), data={
            'grant_type': 'client_credentials',
            'scope': 'all'
        }).json()
        return MendeleySession(
            auth.mendeley,
            token,
            client=auth.client
        )
