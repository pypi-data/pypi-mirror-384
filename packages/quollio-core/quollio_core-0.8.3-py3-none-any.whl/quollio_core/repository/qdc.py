import base64
import json
import logging
import time
from typing import Dict, List

import jwt
import requests  # type: ignore
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from quollio_core.models.qdc import DataSourceMetadataResponseBody, GetImportURLRequest, GetImportURLResponse

logger = logging.getLogger(__name__)


class QDCExternalAPIClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_token = self._get_auth_token()
        self.session = self._gen_session()

    def _get_auth_token(self) -> str:
        """
        [NOTE]
        Tried to find a package for oauth0 client credentials flow,
        but any of them contains bugs or lacks of features to handle the token refresh when it's expired
        """

        url = f"{self.base_url}/oauth2/token"
        creds = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(creds.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_creds}", "Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "scope": "api.quollio.com/beta:admin",
        }
        try:
            res = requests.post(url, headers=headers, data=payload)
            res.raise_for_status()
            return json.loads(res.text).get("access_token")
        except ConnectionError as ce:
            logger.error("Connection Error: {}".format(ce))
            raise
        except HTTPError as he:
            logger.error("HTTP Error: {}".format(he))
            raise
        except Timeout as te:
            logger.error("Timeout Error: {}".format(te))
            raise
        except RequestException as re:
            logger.error("RequestException Error: {}".format(re))
            raise

    def _refresh_token_if_expired(self):
        decoded_data = jwt.decode(self.auth_token, options={"verify_signature": False})
        if decoded_data.get("exp") < time.time():
            self.auth_token = self._get_auth_token()

    def _gen_session(self) -> requests.Session:
        retry = requests.adapters.Retry(total=9, backoff_factor=1, status_forcelist=[429, 500, 503, 504])
        session = requests.Session()
        session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retry))
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry))
        return session

    def get_export_url(self, datasource_id: str) -> GetImportURLResponse:
        self._refresh_token_if_expired()
        headers = {"content-type": "application/json", "authorization": f"Bearer {self.auth_token}"}
        endpoint = "{base_url}/v2/sources/{dsrc_id}/export-avro".format(base_url=self.base_url, dsrc_id=datasource_id)
        try:
            res = self.session.post(endpoint, headers=headers, data={})
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce} global_id: {datasource_id}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he} global_id: {datasource_id}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te} global_id: {datasource_id}.")
        except RequestException as re:
            logger.error(f"RequestException Error: {re} global_id: {datasource_id}.")
        else:
            res = json.loads(res.text)
            location = res.get("data").get("location")
            return location

    def download_file(self, url: str) -> requests.Response:
        self._refresh_token_if_expired()

        try:
            res = self.session.get(url)
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te}")
        except RequestException as re:
            logger.error(f"RequestException Error: {re}")
        else:
            return res

    def get_import_url(self, datasource_id: str, payload: GetImportURLRequest) -> GetImportURLResponse:
        self._refresh_token_if_expired()
        headers = {"content-type": "application/json", "authorization": f"Bearer {self.auth_token}"}
        endpoint = "{base_url}/v2/sources/{dsrc_id}/import".format(base_url=self.base_url, dsrc_id=datasource_id)
        try:
            payload_dict = payload.as_dict()
            res = self.session.post(endpoint, headers=headers, json=payload_dict)
            logger.debug(f"Got the result of import_url request: {res.text}")
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce} global_id: {datasource_id}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he} global_id: {datasource_id}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te} global_id: {datasource_id}.")
        except RequestException as re:
            logger.error(f"RequestException Error: {re} global_id: {datasource_id}.")
        else:
            res = json.loads(res.text)
            datasource_metadata_response = DataSourceMetadataResponseBody(**res.get("data").get("metadata"))
            location = res.get("data").get("location")
            response = GetImportURLResponse(
                location=location, datasource_metadata_response_body=datasource_metadata_response
            )
            return response

    def upload_file(self, url: str, metadata: DataSourceMetadataResponseBody, buffer: bytes):
        self._refresh_token_if_expired()
        headers = {
            "Content-Type": "application/octet-stream",
            "x-amz-meta-user_id": metadata.user_id,
            "x-amz-meta-job_key": metadata.job_key,
            "x-amz-meta-service_name": metadata.service_name,
            "x-amz-meta-source_name": metadata.source_name,
            "x-amz-meta-source_type": metadata.source_type,
            "x-amz-meta-override_logical_name": metadata.override_logical_name,
            "Content-Length": str(len(buffer)),
        }
        try:
            res = self.session.put(url, headers=headers, data=buffer)
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te}")
        except RequestException as re:
            logger.error(f"RequestException Error: {re}")
        else:
            return res.status_code

    def update_stats_by_id(self, global_id: str, payload: Dict[str, List[str]]) -> int:
        self._refresh_token_if_expired()
        headers = {"content-type": "application/json", "authorization": f"Bearer {self.auth_token}"}
        endpoint = f"{self.base_url}/v2/assets/{global_id}/stats"
        try:
            time.sleep(0.5)
            res = self.session.put(endpoint, headers=headers, json=payload)
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce} global_id: {global_id}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he} global_id: {global_id}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te} global_id: {global_id}.")
        except RequestException as re:
            logger.error(f"RequestException Error: {re} global_id: {global_id}.")
        else:
            return res.status_code

    def update_lineage_by_id(self, global_id: str, payload: Dict[str, List[str]]) -> int:
        self._refresh_token_if_expired()
        headers = {"content-type": "application/json", "authorization": f"Bearer {self.auth_token}"}
        endpoint = f"{self.base_url}/v2/lineage/{global_id}"
        try:
            time.sleep(0.5)
            res = self.session.put(endpoint, headers=headers, json=payload)
            res.raise_for_status()
        except ConnectionError as ce:
            logger.error(f"Connection Error: {ce} downstream_global_id: {global_id}.")
        except HTTPError as he:
            logger.error(f"HTTP Error: {he} downstream_global_id: {global_id}.")
        except Timeout as te:
            logger.error(f"Timeout Error: {te} downstream_global_id: {global_id}.")
        except RequestException as re:
            logger.error(f"RequestException Error: {re} downstream_global_id: {global_id}.")
        else:
            return res.status_code


def initialize_qdc_client(api_url: str, client_id: str, client_secret: str) -> QDCExternalAPIClient:
    return QDCExternalAPIClient(base_url=api_url, client_id=client_id, client_secret=client_secret)
