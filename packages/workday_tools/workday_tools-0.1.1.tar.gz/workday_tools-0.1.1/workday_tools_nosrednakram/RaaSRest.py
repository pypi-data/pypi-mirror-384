import yaml
from requests.auth import HTTPBasicAuth, AuthBase
import requests
from urllib.parse import quote_plus
import logging
from requests.models import Response
from typing import Optional

def read_config(config_file: str) -> dict:
    with open(config_file) as f:
        data =  yaml.load(f, Loader=yaml.FullLoader)
        logging.info(f"Loaded config from {config_file}: {data}")
        return data

class RaaSRest:
    """
    Use YAML file to make it easy to use basic auth to access a RaaS from workday.
    """
    _core_url: str
    _auth: AuthBase
    _report_owner: str

    def __init__(self, config_file: str = "workday.yaml"):
        self.logger = logging.getLogger(__name__)
        try:
            cfg = read_config(config_file)
        except FileNotFoundError:
            self.logger.error("No config file found. Default is workday.yaml, read the documentation.")
            raise

        path = cfg.get('path', "/ccx/service/customreport2") + "/"
        environment = cfg.get('environment', 'PROD')
        if environment == "PROD":
            base_url = cfg.get('prod_url', cfg.get('base_url', ''))
        else:
            base_url = cfg.get('devel_url', cfg.get('base_url', ''))

        tenant = cfg.get('tenant', '')
        self._core_url = f"{base_url}{path}{tenant}"
        self._auth = HTTPBasicAuth(cfg.get('account', ''), cfg.get('password', ''))
        self._report_owner = cfg.get('report_owner', cfg.get('account', ''))

        self.logger.info('RaaSRest initialized')

    def report(
        self,
        report: str,
        report_owner_param: Optional[str] = None,
        format: str = "json",
        extra_params: str = ""
    ) -> Response:
        """
        Pull the specified RaaS report and return the result as a requests.Response.
        """
        report_owner = report_owner_param or self._report_owner
        report_owner_path = '/' + quote_plus(report_owner) + '/'

        url = f"{self._core_url}{report_owner_path}{report}?format={format}{extra_params}"
        self.logger.info(f'RaaSRest URL: {url}')
        try:
            response = requests.get(url, auth=self._auth)
            if response.status_code != 200:
                self.logger.warning(f'RaaSRest failed with status code {response.status_code}')
                self.logger.debug(f'RaaSRest response: {response.text}')
            return response
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error connecting to {self._core_url}")
            the_response = Response()
            the_response.status_code = 503
            the_response._content = f'Connection error connecting to {self._core_url}'.encode()
            return the_response
