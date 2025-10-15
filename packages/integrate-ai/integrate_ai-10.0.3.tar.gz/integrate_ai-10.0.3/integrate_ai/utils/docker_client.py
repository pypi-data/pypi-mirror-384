
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""
Module containing docker interface functionality.

This contains a `DockerClient` class that will be used to interface with the docker client on 
  the user's system.
Having a docker client installed on the system is a prerequisite for this to work.
"""

import docker  # type: ignore
from docker.models.images import Image  # type: ignore
from integrate_ai.utils.rest_client import RestClient
from integrate_ai.utils.error_handling import DockerException
from typing import Optional, Dict, List
from distutils.version import LooseVersion
from typing import Any


class DockerClient:
    """Class to interact with docker client.

    This class performs various docker operations such as login, pull, rmi, etc.
    """

    def __init__(self, token: Optional[str] = None, gpu: bool = False, image_name: str = "fl-client"):
        """Initialize.

        Args:
            token (str): IAI token.
        """
        self.token: Optional[str] = token
        self.gpu = gpu
        self.rest_client: Optional[RestClient] = None
        if self.token:
            self.rest_client = RestClient(self.token)
        self.docker_client: docker.DockerClient = docker.from_env()
        self.repo: str = ""
        self.ecr_token: str = ""
        self.ecr_username: str = ""
        self.image_name = image_name

    def login(self) -> Optional[Dict]:
        """Retrieves authentication to connect to ECR repo and performs docker login.

        Returns:
            login_response (Dict): Contains response information returned from docker login.

        Raises:
            DockerException: If error performing docker login command.
        """
        if self.rest_client:
            ecr_response = self.rest_client.get_ecr_token()
            self.ecr_token = ecr_response.get("authorizationToken", "")
            self.repo = ecr_response.get("proxyEndpoint", "")
            self.ecr_username = ecr_response.get("username", "")
            try:
                login_response = self.docker_client.login(
                    username=self.ecr_username,
                    password=self.ecr_token,
                    registry=self.repo,
                )
                return login_response
            except Exception as e:
                raise DockerException(e)
        else:
            raise DockerException("No REST Client available to connect ")

    def get_repo_name(self) -> str:
        """Retrieves the client image name to pull.

        Returns:
            name (str): name of the docker image to retrieve.
        """
        if self.rest_client:
            ecr_repo_response = self.rest_client.get_ecr_repo(image=self.image_name)
        return ecr_repo_response["repo_name"]

    def _auth_dict(self) -> Dict[str, str]:
        """Returns authorization dictionary for docker commands using ECR repo.

        Returns:
            auth_dict (Dict): contains authorization dictionary for ECR connection
        """
        return {"username": self.ecr_username, "password": self.ecr_token}

    def filter_image_by_tag_part(self, image: Image, tag_part: str) -> bool:
        """Determines if `tag_part` is found in image tags.

        Args:
            image (Image): image to check tags for.
            tag_part (str): Checked against image tags to see if is contained in first part of tag.

        Returns:
            tag_part_contained (bool): True if `tag_part` found in tags, False otherwise.
        """
        for tag in image.tags:
            if tag_part == tag.split(":")[0]:
                return True
        return False

    def get_local_versions(self, tag_part: str) -> List[Image]:
        """Returns the local images that contain `tag_part` as part of one of their tags.

        Args:
            tag_part (str): prefix to filter images by.

        Returns:
            image_list (List[Image]): list of images on user's system containing `tag_part`.
        """
        return [image for image in self.docker_client.images.list() if self.filter_image_by_tag_part(image, tag_part)]

    def get_latest_version_of_image(self, images: List[Image]) -> Optional[str]:
        """Returns the latest version number from a list of comparable images.

        Note: If 'latest' is the only version found (no numbered version) or list is empty, will return `None`

        Args:
            images (List[Image]): list of images to search for latest version.

        Returns:
            version_no (str) latest version number found if available. Otherwise `None`.
        """
        local_versions = []
        for image in images:
            for tag in image.tags:
                repo, version = tag.split(":")
                local_versions.append(version)
        non_latest_versions = [el for el in local_versions if not el.startswith("latest")]

        if len(non_latest_versions) > 0:
            return sorted(
                non_latest_versions,
                key=LooseVersion,
                reverse=True,
            )[0]
        else:
            return None

    def get_versions(self):
        """Returns a list of available versions from the ecr repository.

        Returns:
            versions (List[string]): list of available docker images to pull.
        """
        # Split the repository name into the registry and the short form of the repository
        versions_response = self.rest_client.get_ecr_versions(image=self.image_name)
        return versions_response["versions"]

    def delete_images(self, images: List[Image]) -> None:
        """Deletes images contained in a list

        Args:
            images (List[Image]): list of images to delete.
        """
        for image in images:
            self.docker_client.images.remove(image.id, force=True)

    def pull(self, repo: str, tag: str, platform: str = "linux/amd64") -> Dict[str, str]:
        """Pulls docker image corresponding to specified repo and tag.

        Args:
            repo (str): image name to pull.
            tag (str): tag of image to pull.
            platform (str): Platform of image default to linux/amd64
        Returns:
            pull_response (Dict[str,str]): Response Dict returned from docker pull request.

        Raises:
            DockerException: If error in docker pull command.
        """
        try:
            pull_response = self.docker_client.images.pull(
                repository=repo, tag=tag, auth_config=self._auth_dict(), platform=platform
            )
            return pull_response
        except Exception as e:
            raise DockerException(e)

    def get_latest_available_version(self) -> str:
        """Returns the latest available version of the client docker available in repo.

        Returns:
            latest_version (str): latest client image version number available in repo."""

        if self.rest_client:
            is_cpu = self.image_name == "fl-client" and not self.gpu
            version_response = self.rest_client.get_latest_ecr_version(image=self.image_name, is_cpu=is_cpu)
            return version_response["version"]
        else:
            raise DockerException("No REST Client available to connect ")

    def run(self, image: str, detach: bool, options: Dict[str, Any]) -> Optional[Dict]:
        """Starts a container with given image name and configurations.

        Args:
            image str: image name to run the container
            detach bool: whether or not the process should return immediately
            options Dict[str, str]: a dict of options accepted by `docker run` command.

        Returns:
            run_response (Dict[str,str]): Response Dict returned from docker run command.

        Raises:
            DockerException: If error in docker run command.

        """
        try:
            run_response = self.docker_client.containers.run(image, detach=detach, **options)

            return run_response
        except Exception as e:
            raise DockerException(e)

    def get_container(self, container_name):
        """Gets container with given name.

        Args:
            container_name str: name of container we are searching for

        Returns:
            Container: class representation of container object

        Raises:
            DockerException: If error in getting container.

        """
        try:
            return self.docker_client.containers.get(container_name)
        except Exception as e:
            raise DockerException(e)
