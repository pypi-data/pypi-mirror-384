import time
from dataclasses import dataclass
from typing import Optional, cast
from urllib.parse import urljoin
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import requests

from midpoint_cli.client.objects import (
    MidpointConnector,
    MidpointObjectList,
    MidpointObjectType,
    MidpointObjectTypes,
    MidpointOrganization,
    MidpointResource,
    MidpointTask,
    MidpointUser,
    namespaces,
)
from midpoint_cli.client.observer import MidpointCommunicationObserver, NopMidpointCommunicationObserver
from midpoint_cli.client.patch import patch_from_file
from midpoint_cli.client.progress import NopProgressMonitor as NopProgressMonitor
from midpoint_cli.client.progress import ProgressMonitor
from midpoint_cli.client.session import CustomHTTPAdapter, CustomRetryManager


class MidpointServerError(Exception):
    pass


class MidpointUnsupportedOperation(Exception):
    pass


@dataclass
class MidpointClientConfiguration:
    url: str = 'http://localhost:8080/midpoint/'
    username: str = 'administrator'
    password: str = '5ecr3t'


class RestApiClient:
    def __init__(
        self,
        client_configuration: MidpointClientConfiguration,
        observer: Optional[MidpointCommunicationObserver] = None,
    ):
        self.configuration = client_configuration

        if observer is None:
            # No-op observer implementation
            observer = NopMidpointCommunicationObserver()

        session = requests.Session()

        adapter = CustomHTTPAdapter(
            max_retries=CustomRetryManager(connect=1000, total=1000, observer=observer), observer=observer
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        self.requests_session = session

    def get_element(self, element_class: MidpointObjectType, element_oid: str) -> str:
        assert element_class.endpoint is not None, f'Element class {element_class} has no endpoint'
        response = self.requests_session.get(
            url=urljoin(self.configuration.url, 'ws/rest/' + element_class.endpoint + '/' + element_oid),
            auth=(self.configuration.username, self.configuration.password),
        )

        return cast(str, response.content.decode())

    def delete(self, element_class: MidpointObjectType, element_oid: str) -> str:
        assert element_class.endpoint is not None, f'Element class {element_class} has no endpoint'
        response = self.requests_session.delete(
            url=urljoin(self.configuration.url, 'ws/rest/' + element_class.endpoint + '/' + element_oid),
            auth=(self.configuration.username, self.configuration.password),
        )

        return cast(str, response.content.decode())

    def get_elements(self, element_class: MidpointObjectType) -> Element:
        assert element_class.endpoint is not None, f'Element class {element_class} has no endpoint'
        url = urljoin(self.configuration.url, 'ws/rest/' + element_class.endpoint)
        response = self.requests_session.get(url=url, auth=(self.configuration.username, self.configuration.password))
        if response.status_code >= 300:
            raise MidpointServerError(f'Server responded with status code {response.status_code} on {url}')

        tree = ElementTree.fromstring(response.content)
        return tree

    def execute_action(self, element_class: MidpointObjectType, element_oid: str, action: str) -> bytes:
        assert element_class.endpoint is not None, f'Element class {element_class} has no endpoint'
        response = self.requests_session.post(
            url=urljoin(self.configuration.url, 'ws/rest/' + element_class.endpoint + '/' + element_oid + '/' + action),
            auth=(self.configuration.username, self.configuration.password),
        )

        return cast(bytes, response.content)

    def put_element(
        self, xml_filename: str, patch_file: Optional[str], patch_write: bool
    ) -> tuple[MidpointObjectType, str]:
        tree_root = self._load_xml(xml_filename)

        root_tag_name = tree_root.tag.split('}', 1)[1] if '}' in tree_root.tag else tree_root.tag  # strip namespace
        object_type = MidpointObjectTypes.find_by_tagname(root_tag_name)

        if not object_type.endpoint:
            raise MidpointUnsupportedOperation(f'Upload of {object_type} is not supported through REST API')

        object_oid = tree_root.attrib['oid']

        with open(xml_filename) as xml_file:
            xml_body = xml_file.read()

            if patch_file is not None:
                xml_body = patch_from_file(xml_body, patch_file, patch_write)

            target_url = urljoin(self.configuration.url, 'ws/rest/' + object_type.endpoint + '/' + object_oid)
            res = self.requests_session.put(
                url=target_url,
                data=xml_body,
                headers={'Content-Type': 'application/xml'},
                auth=(self.configuration.username, self.configuration.password),
            )

            if res.status_code >= 300:
                raise MidpointServerError(f'Error {res.status_code} received from server at {target_url}')

            return object_type, object_oid

    @staticmethod
    def _load_xml(xml_file: str) -> Element:
        tree_root = ElementTree.parse(xml_file).getroot()
        return tree_root


class TaskExecutionFailure(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self):
        return self.message


class MidpointClient:
    def __init__(
        self,
        client_configuration: Optional[MidpointClientConfiguration] = None,
        api_client: Optional[RestApiClient] = None,
        observer: Optional[MidpointCommunicationObserver] = None,
    ):
        if client_configuration is not None:
            self.api_client = RestApiClient(client_configuration, observer=observer)

        if api_client is not None:
            self.api_client = api_client

    def __get_object(self, midpoint_type: MidpointObjectType, oid: str) -> Element:
        response = self.api_client.get_element(midpoint_type, oid)
        tree = ElementTree.fromstring(response)

        status = tree.find('c:status', namespaces)

        if status is not None and status.text == 'fatal_error':
            message_node = tree.find('c:partialResults/c:message', namespaces)
            message = message_node.text if message_node is not None else 'Unknown error'
            raise MidpointServerError(message)

        return tree

    def __get_collection(self, mp_class: MidpointObjectType, local_class: type) -> MidpointObjectList:
        tree = self.api_client.get_elements(mp_class)
        return MidpointObjectList([local_class(entity) for entity in tree])

    def get_tasks(self) -> MidpointObjectList:
        return self.__get_collection(MidpointObjectTypes.TASK.value, MidpointTask)

    def get_resources(self) -> MidpointObjectList:
        return self.__get_collection(MidpointObjectTypes.RESOURCE.value, MidpointResource)

    def get_connectors(self) -> MidpointObjectList:
        return self.__get_collection(MidpointObjectTypes.CONNECTOR.value, MidpointConnector)

    def get_user(self, oid: str) -> MidpointUser:
        user_root = self.__get_object(MidpointObjectTypes.USER.value, oid)
        user = MidpointUser(user_root)
        return user

    def get_users(self) -> MidpointObjectList:
        return self.__get_collection(MidpointObjectTypes.USER.value, MidpointUser)

    def get_orgs(self) -> MidpointObjectList:
        return self.__get_collection(MidpointObjectTypes.ORG.value, MidpointOrganization)

    def task_action(self, task_oid: str, task_action: str, progress_monitor: ProgressMonitor) -> Optional[MidpointTask]:
        self.api_client.execute_action(MidpointObjectTypes.TASK.value, task_oid, task_action)

        if task_action == 'run':
            return self.task_wait(task_oid, progress_monitor)

        return None

    def task_wait(self, task_oid: str, progress_monitor: ProgressMonitor) -> MidpointTask:
        # First, get the initial task state to extract start time
        task_root = self.__get_object(MidpointObjectTypes.TASK.value, task_oid)
        initial_task = MidpointTask(task_root)

        # Set the task start time on the progress monitor before entering
        task_start_time = initial_task.get_start_time()
        progress_monitor.set_task_start_time(task_start_time)

        with progress_monitor as progress:
            # Update with initial progress and statistics
            initial_progress = int(initial_task['Progress'] or '0')
            initial_success = initial_task.get_success_count()
            initial_failure = initial_task.get_failure_count()
            progress.update_with_stats(initial_progress, initial_success, initial_failure)

            # Check if task is already completed
            rstatus = initial_task['Result Status']
            if rstatus != 'in_progress':
                print()
                if rstatus != 'success':
                    raise TaskExecutionFailure('Failed execution of task ' + task_oid + ' with status ' + rstatus)
                return initial_task

            # Continue polling for updates
            while True:
                time.sleep(2)
                task_root = self.__get_object(MidpointObjectTypes.TASK.value, task_oid)
                task = MidpointTask(task_root)

                # Update with progress and statistics
                current_progress = int(task['Progress'] or '0')
                current_success = task.get_success_count()
                current_failure = task.get_failure_count()
                progress.update_with_stats(current_progress, current_success, current_failure)

                rstatus = task['Result Status']

                if rstatus != 'in_progress':
                    print()
                    if rstatus != 'success':
                        raise TaskExecutionFailure('Failed execution of task ' + task_oid + ' with status ' + rstatus)

                    return task

    def test_resource(self, resource_oid: str) -> str:
        response = self.api_client.execute_action(MidpointObjectTypes.RESOURCE.value, resource_oid, 'test')
        tree = ElementTree.fromstring(response)
        status_node = tree.find('c:status', namespaces)
        return status_node.text if status_node is not None and status_node.text is not None else 'unknown'

    def get_xml(self, midpoint_type: MidpointObjectType, oid: str) -> str:
        return self.api_client.get_element(midpoint_type, oid)

    def put_xml(
        self, xml_file: str, patch_file: Optional[str] = None, patch_write: bool = False
    ) -> tuple[MidpointObjectType, str]:
        return self.api_client.put_element(xml_file, patch_file, patch_write)

    def delete(self, midpoint_type: MidpointObjectType, oid: str) -> str:
        return self.api_client.delete(midpoint_type, oid)
