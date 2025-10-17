""" Python client for making API requests to the Altmetrics service.

This will be used to fetch a JWT token using user login information, as well
as use this token to make further API requests.

This will be developed alongside the Altmetrics API to help use this service.
"""

from logging import getLogger
import requests
from requests.auth import HTTPBasicAuth

logger = getLogger(__name__)


def utf8(bytes_value):
    return bytes_value.decode('utf-8')


class AltmetricsClient:

    API_BASE = 'https://altmetrics.operas-eu.org/api'

    def __init__(self, email: str, password: str, api_base: str = API_BASE):
        """Set the base_url and user credentials for the client.

        Args:
            email (str): email for user login on the altmetrics system
            password (str): password for user login on the altmetrics system
            api_base (str): url for the altmetrics API
        """
        self.base_url = api_base
        self.email = email
        self.password = password
        self.api_base = api_base.rstrip('/')
        self.token = None
        self.header = None

        # ## URLs used by this client can be set here
        self.doi_url = f'{self.api_base}/uriset'
        self.event_url = f'{self.api_base}/eventset'

        if not self.token:  # ## get token and set header
            self.set_token()
            self.set_header()

    def get_token(self):
        """Makes a request to the Altmetrics API to get a JWT token."""
        token_url = f'{self.api_base}/get_token'

        response = requests.get(
            token_url,
            auth=HTTPBasicAuth(self.email, self.password)
        )

        if response.status_code != 200:
            raise ValueError(response.content)

        return utf8(response.content)

    def set_token(self):
        """Makes a request to the Altmetrics API to get a JWT token."""
        self.token = self.get_token()

    def set_header(self, token_has_expired=False):
        """Sets Authorization header for the client using the Bearer schema.

        Args:
            token_has_expired (bool): True if token has expired.
        """
        if not self.token or token_has_expired:
            self.set_token()

        self.header = {'Authorization': f'Bearer {self.token}'}

    def register_dois(self, doi_list):
        """Post DOIs to the Altmetrics API.

        Args:
            doi_list (list): list of dicts containing DOIs to be sent

        Returns:
            object: Response returned by API
        """
        response = requests.post(
            self.doi_url,
            json=doi_list,
            headers=self.header
        )

        logger.info(f'Register DOIS, len={len(doi_list)}')

        return response.status_code, response

    def query_dois(self):
        """Check all DOIs associated with user's account. """
        response = requests.get(self.doi_url, headers=self.header)

        return response.status_code, utf8(response.content)

    def fetch_doi(self, doi):
        """Fetch a single DOI associated with a user.

        Returns:
            tuple: status_code and Response returned by API
        """
        response = requests.get(f'{self.doi_url}/{doi}', headers=self.header)

        logger.info(f'FETCH doi, doi={doi}')

        return response.status_code, utf8(response.content)

    def post(self, *args, **kwargs):
        """Authenticated post request. """
        kwargs.setdefault('headers', {}).update(self.header)
        response = requests.post(*args, **kwargs)

        if response.status_code == 401:  # Assume token has expired
            self.set_header(token_has_expired=True)
            kwargs['headers'].update(self.header)
            response = requests.post(*args, **kwargs)

        return response
