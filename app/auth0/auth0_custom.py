from app.configs.auth0_configs import *
from requests import post, get, patch

class Auth0UserManager:
    authToken = None

    def __init__(self):
        pass

    def get_bearer(self):
        headers = {'content-type': 'application/json'}
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'audience': API_IDENT,
            'grant_type': 'client_credentials'
        }
        resp = post(AUTH0_DOMAIN + '/oauth/token', json=data, headers=headers)
        resp.raise_for_status()
        self.authToken = resp.json()['access_token']

    def set_app_metadata(self, auth0_user_id, user_id):
        headers = {
            'authorization': 'Bearer ' + self.authToken,
            'content-type': 'application/json'
        }
        body = {
            'app_metadata': {'app_user_id': user_id}
        }

        resp = patch(API_IDENT + 'users/' + auth0_user_id, headers=headers, json=body)
        resp.raise_for_status()

        return resp.json()