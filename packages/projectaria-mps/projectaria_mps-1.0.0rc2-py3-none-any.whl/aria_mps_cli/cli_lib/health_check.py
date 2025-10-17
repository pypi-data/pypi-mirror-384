# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from asyncio import Task
from typing import Any, Dict, final, Optional

from aria_mps_cli.cli_lib.common import run_subprocess_with_logging
from aria_mps_cli.cli_lib.constants import (
    KEY_VHC_ARIA_GEN1_DEFAULT,
    KEY_VHC_ARIA_GEN2_DEFAULT,
)
from aria_mps_cli.cli_lib.runner_with_progress import RunnerWithProgress
from aria_mps_cli.cli_lib.types import AriaRecording, MpsAriaDevice

logger = logging.getLogger(__name__)


class HealthCheckRunner(RunnerWithProgress):
    """
    Run health check on a given vrs file.
    """

    def __init__(self, recording: AriaRecording) -> None:
        self._recording: AriaRecording = recording

        # Declare for parent class
        self._task: Optional[Task] = None

    @classmethod
    @final
    def get_key(cls, recording: AriaRecording) -> str:
        """
        Get a unique key for this Runner instance.

        Args:
            recording (AriaRecording): The Aria Recording to get the key for.
        Returns:
            A unique key for this Runner instance.
        """

        return f"{recording.path}_{recording.health_check_path}"

    @final
    async def _run(self) -> None:
        """
        Run the health check on this vrs file.
        Repeatedly calling run will await on the same task
        """

        if self._recording.health_check_path.exists():
            logger.info(
                f"Health check found for {self._recording.path}, checking if this is valid"
            )
            try:
                device_type: MpsAriaDevice = self._recording.device_type
                with open(self._recording.health_check_path, "r") as f:
                    vhc_json: Dict[str, Any] = json.load(f)
                if (
                    device_type == MpsAriaDevice.ARIA_GEN1
                    and KEY_VHC_ARIA_GEN1_DEFAULT in vhc_json
                ) or (
                    device_type == MpsAriaDevice.ARIA_GEN2
                    and KEY_VHC_ARIA_GEN2_DEFAULT in vhc_json
                ):
                    logger.info("Health check is valid")
                    return
                logger.error(
                    f"Invalid or older version health check found for {self._recording.path}"
                )
            except Exception as e:
                logger.error(f"Error checking health check validity: {e}")

        logger.info(f"Running health check on {self._recording.path}")
        _, _, _ = await run_subprocess_with_logging(
            "run_vrs_health_check",
            "--path",
            self._recording.path.as_posix(),
            "--output-json",
            self._recording.health_check_path.as_posix(),
            "--print-stats",
            logger_instance=logger,
        )
