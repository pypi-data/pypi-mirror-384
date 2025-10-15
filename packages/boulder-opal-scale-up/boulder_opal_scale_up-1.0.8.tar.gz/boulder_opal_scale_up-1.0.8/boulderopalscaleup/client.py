# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.
"""
Client for the Boulder Opal Scale Up API.
"""

import json
import logging
import os
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any

import grpc
from boulderopalscaleupsdk.agent import Agent, AgentSettings, TaskHandler
from boulderopalscaleupsdk.common.dtypes import (
    DEFAULT_JOB_HISTORY_PAGE,
    DEFAULT_JOB_HISTORY_PAGE_SIZE,
    DEFAULT_JOB_HISTORY_SORT_ORDER,
    JobData,
    JobHistorySortOrder,
    JobId,
    JobSummary,
    SyncClientInterceptor,
)
from boulderopalscaleupsdk.constants import (
    DEFAULT_GRPC_MAX_RECEIVE_MESSAGE_LENGTH,
    DEFAULT_GRPC_MAX_SEND_MESSAGE_LENGTH,
)
from boulderopalscaleupsdk.device.config_loader import DeviceConfigLoader, DeviceInfo
from boulderopalscaleupsdk.device.controller.resolver import ControllerResolverService
from boulderopalscaleupsdk.device.defcal import DefCalData
from boulderopalscaleupsdk.device.device import DeviceData, DeviceSummary
from boulderopalscaleupsdk.device.processor import (
    SuperconductingProcessor,
)
from boulderopalscaleupsdk.device.processor.superconducting_processor import Resonator, Transmon
from boulderopalscaleupsdk.errors import ScaleUpServerError
from boulderopalscaleupsdk.experiments import Experiment
from boulderopalscaleupsdk.grpc_interceptors.auth import AuthInterceptor
from boulderopalscaleupsdk.grpc_interceptors.error import ErrorFormatterInterceptor
from boulderopalscaleupsdk.plotting import Plot
from boulderopalscaleupsdk.protobuf.v1 import (
    agent_pb2,
    device_pb2,
    device_pb2_grpc,
    job_pb2,
    job_pb2_grpc,
    task_pb2,
)
from boulderopalscaleupsdk.routines import Routine
from boulderopalscaleupsdk.solutions import Solution
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct
from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from boulderopalscaleup.auth import get_default_api_key_auth
from boulderopalscaleup.constants import API_KEY_NAME, SERVER_URL
from boulderopalscaleup.controllers._base import Controller
from boulderopalscaleup.plots import Plotter

from .utils import display_element

if TYPE_CHECKING:
    from boulderopalscaleupsdk.common.dtypes import GrpcMetadata
    from qctrlclient import ApiKeyAuth

LOG = logging.getLogger(__name__)


def _get_package_version() -> str:
    """
    Get the version of this package.

    Returns
    -------
    str
        The package version, or "unknown" if it cannot be determined.
    """
    try:
        return metadata.version("boulder-opal-scale-up")
    except metadata.PackageNotFoundError:
        return "unknown"


class QctrlScaleUpClient:
    """
    Q-CTRL Scale Up client providing API access to experiments.
    """

    def __init__(  # noqa: PLR0913
        self,
        controller: Controller,
        app_name: str,
        organization_slug: str,
        api_key: str | None = None,
        local_mode: bool = False,
        api_url: str = SERVER_URL,
    ):
        """
        Initialize the client.

        Parameters
        ----------
        controller : Controller
            The controller instance used to manage QPU-interfacing controllers.
        app_name : str
            The name of the application using the Scale Up API.
        organization_slug : str
            The name of the organization using the Scale Up API.
        api_key : str or None, optional
            The API key for authenticating with the Q-CTRL server. If not provided,
            the key is retrieved from the environment variable `QCTRL_API_KEY`.
        api_url : str, optional
            The URL of the Boulder Opal Scale Up server. Defaults to the value of `SERVER_URL`.
        local_mode : bool, optional
            If True, uses a local unauthenticated server. Defaults to False.

        Raises
        ------
        RuntimeError
            If no API key is provided and the environment variable `QCTRL_API_KEY` is not set.
        """
        self.controller = controller
        self.app_name = app_name
        self.auth: ApiKeyAuth | None
        if local_mode:
            self.auth = None
        else:
            if api_key is None:
                try:
                    api_key = os.environ[API_KEY_NAME]
                except KeyError as error:
                    raise RuntimeError(
                        "No API key provided in environment or function call. "
                        "To call this function without arguments, "
                        f"save your API key's value in the {API_KEY_NAME} "
                        "environment variable.",
                    ) from error
            self.auth = get_default_api_key_auth(api_key)
        self.agent_settings = AgentSettings(agent_id="dummy_agent_id", remote_url=api_url)
        self.request_metadata: GrpcMetadata = [
            ("organization-slug", organization_slug),
            ("client-version", _get_package_version()),
        ]

        self._current_device_name: str | None = None
        self._device_mgr = device_pb2_grpc.DeviceManagerServiceStub(self._create_channel(api_url))
        self._job_mgr = job_pb2_grpc.JobManagerServiceStub(self._create_channel(api_url))
        self._controller_resolver = ControllerResolverService()
        self._silent = False

    @property
    # Read-only to force use of set_current_device which performs checks and is async
    def current_device_name(self) -> str | None:
        return self._current_device_name

    async def create_device(self, device_name: str, device_config: DeviceInfo | Path) -> JobId:
        """
        Create and initialize a device for experiments.

        Parameters
        ----------
        device_name : str
            The name of the device to be created.
        device_config : DeviceInfo or Path
            The device information, or the file path to the device configuration file.

        Raises
        ------
        ScaleUpServerError
            If the device initialization fails on the server.
        """
        if isinstance(device_config, Path):
            device_config = DeviceConfigLoader(device_config).load_device_info()

        if not self._silent:
            _display_message("Creating device...")

        request = device_pb2.CreateRequest(
            app_name=self.app_name,
            device_name=device_name,
            device_data=dict_to_struct(device_config.to_dict()),
        )
        response: device_pb2.CreateResponse = self._device_mgr.Create(
            request,
            metadata=self.request_metadata,
        )
        if not response.done:
            raise ScaleUpServerError("Failed to create device.")

        class _Init(Routine):
            _routine_name: str = "init"

        await self.set_current_device(device_name)
        job_id = await self.run(_Init())
        if not self._silent:
            _display_message(f"Device '{device_name}' created successfully.")
        return job_id

    async def set_current_device(self, device_name: str) -> None:
        """
        Set which device to use in routines and experiments.

        Parameters
        ----------
        device_name : str
            The name of the device to mark as the current device.
        """
        if not self._silent:
            _display_message(f"Setting current device to '{device_name}'...")

        self._silent = True
        # We check device exists by retrieving it
        await self.get_device_data(device_name)
        self._silent = False

        self._current_device_name = device_name
        if not self._silent:
            _display_message(f"Current device set to '{device_name}'.")

    async def get_device_summary(self, device_name: str | None = None) -> DeviceSummary:
        """
        Retrieve the summary of a device.

        Parameters
        ----------
        device_name : str or None, optional
            The device whose summary should be retrieved. Defaults to the current device.

        Returns
        -------
        DeviceSummary
            The summary of the device.

        Raises
        ------
        RuntimeError
            If the device name is not set.
        ScaleUpServerError
            If the response from the server is invalid.
        """
        device_name = self._default_to_current_device(device_name)
        if not self._silent:
            _display_message(f"Generating device summary for device '{device_name}'...")

        request = device_pb2.GetMetadataRequest(device_name=device_name)
        response = self._device_mgr.GetMetadata(request, metadata=self.request_metadata)
        if response is None or not isinstance(response, device_pb2.GetMetadataResponse):
            raise ScaleUpServerError("Failed to retrieve device summary.")

        if not self._silent:
            _display_message(f"Device summary for '{device_name}' generated successfully.")
        return DeviceSummary.model_validate(MessageToDict(response.metadata))

    async def display_device_data_sheet(
        self,
        device_name: str | None = None,
        node_name: str | None = None,
    ) -> None:
        """
        Display a data sheet of the components in the device.

        Parameters
        ----------
        device_name : str or None, optional
            The name of the device to display. Defaults to the current device.
        node_name : str or None, optional
            The name of the node to display. If not provided, all applicable nodes are summarized.
        """
        device_name = self._default_to_current_device(device_name)
        device = await self.get_device_data(device_name)
        if node_name is None:
            display_nodes = {
                key: node
                for key, node in device.qpu.nodes.items()
                if isinstance(node, Resonator | Transmon)
            }
        else:
            node = device.qpu.nodes.get(node_name)
            if not isinstance(node, Resonator | Transmon):
                raise ValueError(f"{node_name} is not a Resonator or Transmon.")
            display_nodes = {node_name: node}
        for name, node in sorted(display_nodes.items()):
            display_element(name, node)

    async def get_device_snapshot(
        self,
        output: Path | str,
        device_name: str | None = None,
    ) -> None:
        """
        Get a snapshot of a device.

        Parameters
        ----------
        output : Path | str
            The output path to save this snapshot.
        device_name : str or None, optional
            The name of the device to snapshot. Defaults to the current device.
        """
        _display_message(
            f"Getting snapshot of device '{self.current_device_name}'.",
        )
        snapshot = await self._get_device_snapshot(device_name=device_name, version=None)
        Path(output).write_text(json.dumps(snapshot))
        snapshot_name = snapshot["device_name"]
        _display_message(f"Snapshot of device '{snapshot_name}' saved to '{output}'.")

    async def _get_device_snapshot(
        self,
        device_name: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        _device_name = device_name or self._current_device_name
        if _device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )
        request = device_pb2.GetSnapshotRequest(
            device_name=_device_name,
            version=version,
        )
        resp: device_pb2.GetSnapshotResponse = self._device_mgr.GetSnapshot(
            request,
            metadata=self.request_metadata,
        )
        return MessageToDict(resp.data)

    async def set_device_snapshot(
        self,
        snapshot: Path | str,
        device_name: str | None = None,
    ) -> None:
        """
        Sets the state of a device by applying the snapshot obtained from `get_snapshot`.

        Parameters
        ----------
        snapshot : Path | str
            The path to a snapshot file.
        device_name : str or None, optional
            The name of the device to apply the snapshot. Defaults to the current device.
        """
        _display_message(
            f"Applying snapshot '{snapshot}' to device '{self.current_device_name}'.",
        )
        _snapshot_dict = json.loads(Path(snapshot).read_text())
        await self._set_device_snapshot(_snapshot_dict, device_name=device_name)
        _display_message(
            f"Snapshot '{snapshot}' applied to device '{self.current_device_name}' successfully.",
        )

    async def _set_device_snapshot(
        self,
        snapshot: dict[str, Any],
        device_name: str | None = None,
    ) -> dict[str, Any]:
        _device_name = device_name or self._current_device_name
        if _device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )
        request = device_pb2.SetSnapshotRequest(
            device_name=_device_name,
            data=dict_to_struct(snapshot),
        )
        resp: device_pb2.SetSnapshotResponse = self._device_mgr.SetSnapshot(
            request,
            metadata=self.request_metadata,
        )
        return MessageToDict(resp)

    @staticmethod
    def display(  # noqa: C901
        data: DeviceSummary | JobSummary | JobData | list[DeviceSummary] | list[JobSummary],
    ) -> None:
        console = Console()
        if isinstance(data, JobData):
            for display_item in data.get_display_items():
                if isinstance(display_item, Plot):
                    Plotter(display_item).figure.show()
                else:
                    console.print(display_item)
            return

        data_list = data if isinstance(data, list) else [data]

        if len(data_list) == 0:
            raise ValueError("Data cannot be an empty list.")

        data_type = type(data_list[0])
        if not isinstance(data_list[0], DeviceSummary | JobSummary):
            raise TypeError(
                f"Invalid data to display. Got {data_type.__name__}.",
            )

        if not all(isinstance(item, data_type) for item in data_list):
            raise TypeError(
                f"All items in the list must be of the same {data_type.__name__}.",
            )

        title = ""
        match data_list[0]:
            case JobSummary():
                title = "Job summary"
            case DeviceSummary():
                title = "Device summary"

        _data = [element.model_dump() for element in data_list]

        table = Table(title=title)
        keys = _data[0].keys()
        for key in keys:
            table.add_column(str(key))

        for item in _data:
            row = [str(item[key]) for key in keys]
            table.add_row(*row)

        console.print(table)

    async def get_device_data(
        self,
        device_name: str | None = None,
    ) -> DeviceData:
        """
        Get latest data for a device.

        Parameters
        ----------
        device_name : str or None, optional
            The name of the device. Defaults to the current device.
        """
        device_name = self._default_to_current_device(device_name)

        if not self._silent:
            _display_message(f"Retrieving data for device '{device_name}'...")

        request = device_pb2.GetDataRequest(device_name=device_name)
        response: device_pb2.GetDataResponse = self._device_mgr.GetData(
            request,
            metadata=self.request_metadata,
        )
        if (
            response.processor_data is None
            or response.controller_data is None
            or response.defcals is None
        ):
            raise ScaleUpServerError(f"Failed to retrieve {device_name} device data.")

        if not self._silent:
            _display_message(f"Data for device '{device_name}' retrieved successfully.")

        superconducting_processor = SuperconductingProcessor.from_dict(
            MessageToDict(response.processor_data),
        )
        controller_info = (
            self._controller_resolver.resolve_controller_info_from_controller_data_struct(
                response.controller_data,
            )
        )
        defcals = {}
        for item in response.defcals:
            defcal_data = DefCalData(**MessageToDict(item))
            defcals[(defcal_data.gate, tuple(defcal_data.addr))] = defcal_data

        return DeviceData(
            qpu=superconducting_processor,
            controller_info=controller_info,
            _defcals=defcals,
        )

    async def update_device(self, new_processor_details: SuperconductingProcessor) -> None:
        """
        Update the current device's processor information.

        Parameters
        ----------
        new_processor_details : SuperconductingProcessor
            The new processor information for the current device.

        Raises
        ------
        RuntimeError
            If no current device has been set.
        """
        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )

        if not self._silent:
            _display_message(f"Updating device '{self.current_device_name}'...")

        request = device_pb2.UpdateRequest(
            device_name=self.current_device_name,
            processor_data=ParseDict(new_processor_details.to_dict(), Struct()),
        )
        response: device_pb2.UpdateResponse = self._device_mgr.Update(
            request,
            metadata=self.request_metadata,
        )
        if response is None or not isinstance(response, device_pb2.UpdateResponse):
            raise ScaleUpServerError("Invalid response received when updating device.")

        if not self._silent:
            _display_message(f"Device '{self.current_device_name}' updated successfully.")

    async def delete_device(self, device_name: str) -> None:
        """
        Delete the specified device.

        Parameters
        ----------
        device_name : str
            The name of the device to delete.
        """

        if not self._silent:
            _display_message(f"Deleting device '{device_name}'...")
        if not self._delete_device_from_server(device_name):
            raise ScaleUpServerError(f"Failed to delete device '{device_name}' from server.")

        if self.current_device_name == device_name:
            self._current_device_name = None

    async def get_devices(self) -> list[DeviceSummary]:
        """
        Retrieve a summary for all devices.

        Returns
        -------
        list[DeviceSummary]:
            The information about the devices.
        """
        if not self._silent:
            _display_message("Retrieving summary for all devices...")

        async def _get_page(next_cursor: str | None) -> tuple[list[DeviceSummary], str | None]:
            request = device_pb2.GetAllDevicesMetadataRequest(
                limit=20,
                next_cursor=next_cursor,
            )
            response = self._device_mgr.GetAllDevicesMetadata(
                request,
                metadata=self.request_metadata,
            )
            if response is None or not isinstance(
                response,
                device_pb2.GetAllDevicesMetadataResponse,
            ):
                raise ScaleUpServerError("Invalid response when attempting to get device summary.")
            summaries = [
                DeviceSummary.model_validate(MessageToDict(metadata))
                for metadata in response.metadatas
            ]
            next_cursor = (
                response.next_cursor
                if response.next_cursor is not None and len(response.next_cursor) > 0
                else None
            )
            return summaries, next_cursor

        summaries, next_cursor = await _get_page(None)
        while next_cursor is not None:
            _summaries, next_cursor = await _get_page(next_cursor)
            summaries.extend(_summaries)

        if not self._silent:
            _display_message("Summary for all devices retrieved successfully.")

        return summaries

    def _default_to_current_device(self, device_name: str | None) -> str:
        if isinstance(device_name, str):
            return device_name

        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device has been set. Call {self.set_current_device.__name__} first.",
            )

        return self.current_device_name

    def _delete_device_from_server(self, device_name: str) -> bool:
        request = device_pb2.DeleteRequest(device_name=device_name)
        response = self._device_mgr.Delete(request, metadata=self.request_metadata)
        if response is None or not isinstance(response, device_pb2.DeleteResponse):
            LOG.error("Invalid response from server when attempting to delete device")
            return False
        return response.done

    def _get_channel_interceptors(self) -> list:
        """
        Get the interceptors for the gRPC channel.
        """
        interceptors: list[SyncClientInterceptor] = []
        if os.getenv("QCTRL_ENABLE_GRPC_FRIENDLY_ERRORS", "true").lower() == "true":
            interceptors.append(ErrorFormatterInterceptor(include_code=False))
        if self.auth:
            interceptors.append(AuthInterceptor(self.auth))
        return interceptors

    def _create_channel(self, api_url: str) -> grpc.Channel:
        """
        Create a gRPC channel.
        """
        grpc_max_send_message_length = os.getenv(
            "GRPC_MAX_SEND_MESSAGE_LENGTH",
            DEFAULT_GRPC_MAX_SEND_MESSAGE_LENGTH,
        )
        grpc_max_receive_message_length = os.getenv(
            "GRPC_MAX_RECEIVE_MESSAGE_LENGTH",
            DEFAULT_GRPC_MAX_RECEIVE_MESSAGE_LENGTH,
        )
        options = [
            ("grpc.max_send_message_length", grpc_max_send_message_length),
            ("grpc.max_receive_message_length", grpc_max_receive_message_length),
        ]
        host = api_url.split(":")[0]
        if host in ["localhost", "127.0.0.1", "0.0.0.0", "::"]:
            channel = grpc.insecure_channel(api_url, options=options)
        else:
            channel = grpc.secure_channel(api_url, grpc.ssl_channel_credentials(), options=options)
        return grpc.intercept_channel(channel, *self._get_channel_interceptors())

    async def enable(self, element: str, *others: str) -> None:
        """
        Enable specified elements for running experiments.

        By default, experiments can target any element on the device. This method
        restricts targeting to only the specified elements, effectively disabling
        all others for experiment runs.

        Parameters
        ----------
        element : str
            Element to enable.
        *others : str
            Additional elements to enable.
        """
        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )
        request = device_pb2.MaskRequest(
            mode=device_pb2.SELECTION_MODE_ITEMS,
            device_name=self.current_device_name,
            elements=[element, *others],
        )
        response: device_pb2.UpdateResponse = self._device_mgr.Mask(
            request,
            metadata=self.request_metadata,
        )
        if response is None or not isinstance(response, device_pb2.MaskResponse):
            raise ScaleUpServerError("Invalid response received when masking elements.")

    async def enable_all(self) -> None:
        """
        Enable all elements for running experiments.

        This method clears any previous restrictions set by `enable` or `disable`,
        making all elements on the device available for experiment targeting.
        """
        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )
        request = device_pb2.MaskRequest(
            mode=device_pb2.SELECTION_MODE_ALL,
            device_name=self.current_device_name,
        )
        response: device_pb2.UpdateResponse = self._device_mgr.Mask(
            request,
            metadata=self.request_metadata,
        )
        if response is None or not isinstance(response, device_pb2.MaskResponse):
            raise ScaleUpServerError("Invalid response received when masking elements.")

    async def disable(self, element: str, *others: str) -> None:
        """
        Disable specified elements from running experiments.

        By default, experiments can target any element on the device. This method
        prevents the specified elements from being used in experiments, while all
        other elements remain enabled.

        Parameters
        ----------
        element : str
            The primary element to disable.
        *others : str
            Additional elements to disable. Accepts any number of additional
            string arguments.
        """
        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )
        request = device_pb2.UnmaskRequest(
            device_name=self.current_device_name,
            elements=[element, *others],
        )
        response: device_pb2.UpdateResponse = self._device_mgr.Unmask(
            request,
            metadata=self.request_metadata,
        )
        if response is None or not isinstance(response, device_pb2.UnmaskResponse):
            raise ScaleUpServerError("Invalid response received when masking elements.")

    async def run(self, job: Experiment | Routine | Solution) -> JobId:
        """
        Execute an experiment, a routine, or a solution.

        Parameters
        ----------
        job : Experiment or Routine or Solution
            The experiment, routine, or solution to run.

        Returns
        -------
        JobId
            The job ID of the executed job.
        """

        if self.current_device_name is None:
            raise RuntimeError(
                f"No current device set. Call {self.set_current_device.__name__} first.",
            )

        self.agent = Agent(
            self.agent_settings,
            AgentTaskHandler(self),
            grpc_interceptors=self._get_channel_interceptors(),
        )

        match job:
            case Experiment():
                name = job.experiment_name
            case Routine():
                name = job.routine_name
            case Solution():
                name = job.solution_name

        job_id = await self.agent.start_session(
            app=self.app_name,
            metadata=self.request_metadata,
            device_name=self.current_device_name,
            routine=name,
            data=dict_to_struct(job.model_dump()),
        )

        if job_id is None:
            raise ScaleUpServerError("Failed to execute the job.")

        return job_id

    async def run_experiment(self, experiment: Experiment) -> JobId:
        """
        Execute an experiment.

        Parameters
        ----------
        experiment : Experiment
            The object containing the parameters for the experiment to be executed.

        Returns
        -------
        JobId
            The job ID of the executed experiment.

        Raises
        ------
        RuntimeError
            If the device name is not set before running the experiment.
        """

        return await self.run(experiment)

    async def run_routine(self, routine: Routine) -> JobId:
        """
        Execute a routine.

        Parameters
        ----------
        routine : Routine
            The object containing the parameters for the routine to be executed.

        Returns
        -------
        JobId
            The job ID of the executed routine.

        Raises
        ------
        RuntimeError
            If the current device name is not set before running the routine.
        """
        return await self.run(routine)

    async def run_solution(self, solution: Solution) -> JobId:
        """
        Execute a solution.

        Parameters
        ----------
        solution: Solution
            The object containing the parameters for the solution to be executed.

        Returns
        -------
        JobId
            The job ID of the executed solution.

        Raises
        ------
        RuntimeError
            If the current device name is not set before running the solution.
        """
        return await self.run(solution)

    async def get_job_data(self, job_id: str) -> JobData:
        """
        Retrieves details about a specific job executed on the device, such as
        its status, execution results, and associated metadata.

        Parameters
        ----------
        job_id : str
            The ID of the job to retrieve.

        Returns
        -------
        JobData
            The job data.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.
        """
        if not self._silent:
            _display_message(f"Retrieving data for job '{job_id}'...")

        response = self._job_mgr.Get(
            job_pb2.GetRequest(job_id=job_id),
            metadata=self.request_metadata,
        )
        if response is None:
            raise ScaleUpServerError("Invalid response.")
        if not isinstance(response, job_pb2.GetResponse):
            raise ScaleUpServerError("Unexpected response type.")

        if not self._silent:
            _display_message(f"Retrieved data for job '{job_id}'.")
        return JobData.model_validate(MessageToDict(response.job_data))

    async def get_jobs(
        self,
        device_name: str | None = None,
        job_name: str | None = None,
        page: int = DEFAULT_JOB_HISTORY_PAGE,
        limit: int = DEFAULT_JOB_HISTORY_PAGE_SIZE,
        sort_order: JobHistorySortOrder = DEFAULT_JOB_HISTORY_SORT_ORDER,
    ) -> list[JobSummary]:
        """
        Retrieves all the jobs that have been previously executed on the given device.

        Parameters
        ----------
        device_name : str
            The name of the device to filter the history by. Defaults to current.
        job_name : str, optional
            The name of the job to filter the history by. Defaults to None.
        page : int, optional
            The page number to retrieve. Defaults to 1.
        limit : int, optional
            The number of jobs to retrieve per page. Defaults to 10.
        sort_order : JobHistorySortOrder, optional
            The sort order for the results.
            Defaults to reverse chronological.

        Returns
        -------
        list[JobSummary]
            The history of jobs run.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.
        """
        device_name = self._default_to_current_device(device_name)

        if not self._silent:
            _display_message(f"Retrieving jobs for device '{device_name}'...")

        response = self._job_mgr.List(
            job_pb2.ListRequest(
                device_name=device_name,
                job_name=job_name,
                page=page,
                limit=limit,
                sort_order=sort_order.value,
            ),
            metadata=self.request_metadata,
        )
        if response is None:
            raise ScaleUpServerError("Invalid response.")
        if not isinstance(response, job_pb2.ListResponse):
            raise ScaleUpServerError("Unexpected response type.")

        if not self._silent:
            _display_message(
                f"Retrieved jobs for device '{device_name}'.",
            )
        return [JobSummary.model_validate(MessageToDict(job)) for job in response.jobs]

    async def get_job_summary(self, job_id: str) -> JobSummary:
        """
        Retrieves a summary of a specific job executed on the device.

        Parameters
        ----------
        job_id : str
            The ID of the job to retrieve.

        Returns
        -------
        JobSummary
            The job summary.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.
        """
        if not self._silent:
            _display_message(f"Retrieving summary for job '{job_id}'...")

        response = self._job_mgr.GetSummary(
            job_pb2.GetSummaryRequest(job_id=job_id),
            metadata=self.request_metadata,
        )
        if response is None:
            raise ScaleUpServerError("Invalid response.")
        if not isinstance(response, job_pb2.GetSummaryResponse):
            raise ScaleUpServerError("Unexpected response type.")

        if not self._silent:
            _display_message(f"Retrieved summary for job '{job_id}'.")
        return JobSummary.model_validate(MessageToDict(response.job_summary_data))


class AgentTaskHandler(TaskHandler):
    def __init__(self, client: QctrlScaleUpClient) -> None:
        self._client = client

    async def handle(
        self,
        request: agent_pb2.RunProgramRequest
        | agent_pb2.RunQuantumMachinesMixerCalibrationRequest
        | agent_pb2.DisplayResultsRequest
        | agent_pb2.AskRequest,
    ) -> (
        agent_pb2.RunProgramResponse
        | agent_pb2.RunQuantumMachinesMixerCalibrationResponse
        | agent_pb2.DisplayResultsResponse
        | agent_pb2.AskResponse
        | task_pb2.TaskErrorDetail
    ):
        match request:
            case agent_pb2.RunProgramRequest():
                return await self._client.controller.run_program(request, self._client)
            case agent_pb2.RunQuantumMachinesMixerCalibrationRequest():
                return await self._client.controller.run_mixer_calibration(request, self._client)
            case agent_pb2.DisplayResultsRequest():
                return await _display_results(request)
            case agent_pb2.AskRequest():
                return await _ask_user(request)


@dataclass
class CalibrationError:
    message: str


async def _display_results(
    results: agent_pb2.DisplayResultsRequest,
) -> agent_pb2.DisplayResultsResponse:
    """
    Display results to the user.
    """

    LOG.info("Displaying results")

    if results.plots is not None:
        for plot in results.plots:
            plot_data: Plot = TypeAdapter(Plot).validate_json(plot)
            Plotter(plot_data).figure.show()

    if results.message is not None:
        _display_message(results.message)

    return agent_pb2.DisplayResultsResponse()


async def _handle_yes_no_ask(ask: agent_pb2.AskRequest) -> agent_pb2.AskResponse:
    """
    Handle yes/no questions from the user.
    """
    while True:
        response = input(f"{ask.message}: ").strip().lower()
        if response in ("y", "yes"):
            return agent_pb2.AskResponse(response="y")
        if response in ("n", "no"):
            return agent_pb2.AskResponse(response="n")
        _display_message("Please answer with 'y' or 'n'.")


async def _ask_user(ask: agent_pb2.AskRequest) -> agent_pb2.AskResponse:
    """
    Ask user interactively.
    """
    _display_message(ask.message)
    match ask.expected_response_type:
        case "yes_no":
            return await _handle_yes_no_ask(ask)
        case _:
            raise ScaleUpServerError(
                f"Unknown expected response type '{ask.expected_response_type}'",
            )


def dict_to_struct(dictionary: dict) -> Struct:
    result = Struct()
    result.update(dictionary)
    return result


def _display_message(message: str) -> None:
    console = Console()
    console.is_jupyter = False
    console.print(message)
