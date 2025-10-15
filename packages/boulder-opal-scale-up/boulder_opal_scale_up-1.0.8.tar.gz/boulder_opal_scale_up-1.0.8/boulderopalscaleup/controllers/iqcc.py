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

import json
import logging
from typing import TYPE_CHECKING, cast

import numpy as np
import qm
from boulderopalscaleupsdk.device.controller.quantum_machines import QuaProgram
from boulderopalscaleupsdk.protobuf.v1 import agent_pb2
from google.protobuf.struct_pb2 import Struct
from iqcc_cloud_client import IQCC_Cloud
from pydantic.dataclasses import dataclass
from pydantic.main import IncEx

from boulderopalscaleup.controllers import Controller

LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from boulderopalscaleup.client import QctrlScaleUpClient


@dataclass
class CalibrationError:
    message: str


class IQCCloudController(Controller):
    def __init__(self, iqcc_client: IQCC_Cloud):
        self.iqcc_client = iqcc_client

    async def run_program(
        self,
        program_request: agent_pb2.RunProgramRequest,
        client: "QctrlScaleUpClient",  # noqa: ARG002
    ) -> agent_pb2.RunProgramResponse:
        LOG.info("Running experiment task %s", program_request)

        qua_program: QuaProgram = QuaProgram.loads(program_request.program)

        # Defined as IncEx so linter is happy.
        exclude_fields: IncEx = cast(
            IncEx,
            {
                "qm_version": True,
                "controllers": {
                    "__all__": {
                        "fems": {
                            "__all__": {
                                "analog_outputs": {
                                    "__all__": {
                                        "filter": {
                                            "feedback": True,
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        config = qua_program.config.root.model_dump_json(exclude=exclude_fields, exclude_none=True)

        LOG.info("Executing program.")
        iqcc_results = self.iqcc_client.execute(
            qm.Program(program=qua_program.program),
            qua_config=json.loads(config),
        )

        LOG.info("Handling results.")
        measurement_data = iqcc_results["result"]

        def _convert(array):
            return np.asarray(array).astype(float).tolist()

        raw_data = {k: _convert(v) for k, v in measurement_data.items()}

        raw_data_struct = Struct()
        raw_data_struct.update(raw_data)
        return agent_pb2.RunProgramResponse(raw_data=raw_data_struct)

    async def run_mixer_calibration(
        self,
        calibration_request: agent_pb2.RunQuantumMachinesMixerCalibrationRequest,
        client: "QctrlScaleUpClient",
    ) -> agent_pb2.RunQuantumMachinesMixerCalibrationResponse:
        """
        Run a mixer calibration on the device.
        """
        raise NotImplementedError("Mixer calibration is not implemented for IQCC Cloud controller.")
