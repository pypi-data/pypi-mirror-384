
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""
Module containing REST interface functionality.

This contains a `RestClient` class that will be used to interface with the IAI REST API.
"""

import jwt
import requests
from typing import Any, Dict
from integrate_ai.utils.error_handling import check_for_IntegrateAIException
import os


class RestClient:
    """Client class for interacting with the integrate.ai API.

    This class includes functionality for performing various operations using
      the integrate.ai REST API.
    This class requires a valid token before it can perform its operations.
    """

    def __init__(self, token: str):
        """Initiates a client given a valid decoded IAI token object.

        Args:
            token (str): IAI token."""

        self.auth_token: str = token
        decoded_token: Dict[str, str] = self._decode_jwt_token(token=token)
        self.customer: str = decoded_token["customer"]
        self.env: str = decoded_token["env"]
        self.api_url: str = self._get_api_endpoint()
        self.gateway_url: str = self._get_gateway_endpoint()

    def _headers(self) -> Dict[str, str]:
        """Add authenticating headers for use with REST API."""

        header = {"content-type": "application/json"}
        header["Authorization"] = f"Bearer {self.auth_token}"
        return header

    def _decode_jwt_token(self, token: str, secret=None, verify_signature: bool = False) -> Dict[str, str]:
        """Decodes a JWT token."""
        decoded_token = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_signature": verify_signature},
        )
        return decoded_token

    def _get_api_endpoint(self) -> str:
        """Returns API endpoint."""

        return os.environ.get("IAI_DEBUG_API_URL") or f"https://iai-api-{self.customer}-{self.env}.integrateai.net"

    def _get_gateway_endpoint(self) -> str:
        """Returns Gateway endpoint."""

        return (
            os.environ.get("IAI_DEBUG_GATEWAY_URL")
            or f"https://iai-fl-gateway-{self.customer}-{self.env}.integrateai.net"
        )

    def make_get_request(self, url: str, body={}, headers=None) -> requests.Response:
        """Performs a GET request using client.

        Args:
            url (str): URL to make GET request to.
            body (Dict): body to include in GET request.
            headers (Dict): The headers to be added to the GET request.
                Defaults to the integrate.ai API Authorization headers.

        Returns:
            response (requests.Response): response object from GET request.

        Raises:
            IntegrateAIException: If error in GET request."""
        request_headers = self._headers()
        if headers:
            request_headers.update(headers)
        response = requests.get(url, headers=request_headers, json=body)
        check_for_IntegrateAIException(response)
        return response

    def get_ecr_token(self) -> Dict[str, str]:
        """Retrieves an ECR token using IAI token.

        Returns:
            ecr_response (Dict[str,str]): response to ECR GET request."""
        url = f"{self.api_url}/fl/ecr/token"
        ecr_response = self.make_get_request(url).json()

        return ecr_response

    def get_ecr_repo(self, image: str) -> Dict[str, str]:
        """Retrieves the ecr repo name for a package"""
        url = f"{self.api_url}/fl/ecr/{image}/repo"
        return self.make_get_request(url).json()

    def get_ecr_versions(self, image: str) -> Dict[str, str]:
        """Retrieves the versions of an image from the ecr repo"""
        url = f"{self.api_url}/fl/ecr/{image}/list"
        return self.make_get_request(url).json()

    def get_latest_ecr_version(self, image: str, is_cpu: bool) -> Dict[str, str]:
        """Retrieves the latest version of an image in ecr"""
        url = f"{self.api_url}/fl/ecr/{image}/latest"
        if is_cpu:
            url += "?cpu"
        return self.make_get_request(url).json()

    def get_pip_install_command(self, version="", package="") -> Dict[str, str]:
        """Get pip install command to install sdk.
        Args:
            version (str): Version of sdk to install
            package (str): Package name to install.
        Returns:
                A Dict of the form
                ```
                {
                    "pipInstallCommand":"<pip_install_command>",
                }
                ```
        Raises:
            IntegrateAIException: Customized IntegrateAI exception for the HTTP Exception.
        """
        url = f"{self.api_url}/fl/pip/{package}"
        if version:
            url += f"/{version}"
        response = requests.get(
            url,
            headers=self._headers(),
        )
        check_for_IntegrateAIException(response=response)

        return response.json()

    def get_package_versions(self, package="") -> Dict[str, Any]:
        """Get package versions.
        Args:
            package (str): Name of package that has a list of available versions.
        Returns:
                A Dict of the form
                ```
            {
                "package_name": "<package-name>",
                "package_versions": [
                    {
                        "version": <version_number_1>,
                        "revision": <revision_string>,
                        "status": "Published"
                    },
                    {
                        "version": <version_number_2>,
                        "revision": <revision_string>,
                        "status": "Published"
                    }
                ]
            }
                ```
        Raises:
            IntegrateAIException: Customized IntegrateAI exception for the HTTP Exception.
        """
        url = f"{self.api_url}/fl/pip/{package}/list"
        response = requests.get(
            url,
            headers=self._headers(),
        )
        check_for_IntegrateAIException(response=response)

        return response.json()

    def get_taskrunner_info(self, taskrunner_name) -> Dict[str, Any]:
        """Get taskrunner info.
        Args:
            taskrunner_name (str): Name of the taskrunner
        Returns:
                List of Taskrunner info
        Raises:
            IntegrateAIException: Customized IntegrateAI exception for the HTTP Exception.
        """
        url = f"{self.api_url}/taskrunners"
        params = {"name": taskrunner_name}
        response = requests.get(url, headers=self._headers(), params=params)
        check_for_IntegrateAIException(response=response)
        return response.json()

    def register_on_prem_taskrunner(self, taskrunner_name) -> Dict[str, Any]:
        """Get package versions.
        Args:
            package (str): Name of package that has a list of available versions.
        Returns:
                A Dict of the form
                ```
            {
                "proxy_info" : {"iai_forward_proxy_http_url" : "http://iai-proxy-ca-central-1-prod.integrateai.net:8888"}
                "activation_id": <activation_id>,
                "activation_code": <activation_code>,
                "region": <region>,
                "cluster": <cluster>
            }
                ```
        Raises:
            IntegrateAIException: Customized IntegrateAI exception for the HTTP Exception.
        """
        url = f"{self.api_url}/taskrunners/{taskrunner_name}/activate"
        response = requests.post(
            url,
            headers=self._headers(),
        )
        check_for_IntegrateAIException(response=response)

        return response.json()

    def deregister_on_prem_taskrunner(self, taskrunner_name, instance_id) -> Dict[str, Any]:
        """Get package versions.
        Args:
            package (str): Name of package that has a list of available versions.
        Returns:
                A Dict of the form
                ```
            {
            }
                ```
        Raises:
            IntegrateAIException: Customized IntegrateAI exception for the HTTP Exception.
        """
        url = f"{self.api_url}/taskrunners/{taskrunner_name}/deregister"
        data = {"instance_id": instance_id}
        response = requests.post(url, headers=self._headers(), json=data)
        check_for_IntegrateAIException(response=response)

        return response.json()
