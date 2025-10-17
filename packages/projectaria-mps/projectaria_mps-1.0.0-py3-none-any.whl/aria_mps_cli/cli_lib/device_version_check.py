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

import asyncio
import logging
import sys
from asyncio import Task
from typing import final, Optional

from aria_mps_cli.cli_lib.common import run_subprocess_with_logging
from aria_mps_cli.cli_lib.runner_with_progress import RunnerWithProgress
from aria_mps_cli.cli_lib.types import AriaRecording, MpsAriaDevice

logger = logging.getLogger(__name__)


class DeviceVersionCheckRunner(RunnerWithProgress):
    """
    Run device version check on a given vrs file.
    """

    _semaphone: asyncio.Semaphore = asyncio.Semaphore(4)

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

        return f"{recording.path}"

    @final
    async def _run(self) -> MpsAriaDevice:
        """
        Infer the device type from the vrs file.
        """
        async with self._semaphone:
            logger.debug(f"Running device type check on {self._recording.path}")

            # We use a python script to get the device type from the vrs file.
            # This is because calling the api directly from python prints debug spew to stdout
            # and messes up the textual UI.
            # This approach is not ideal, but it works for now, until we have a reliable way to suppress the debug spew.
            # from projectaria_tools
            script = """
import sys
from projectaria_tools.core.data_provider import create_vrs_data_provider

print(create_vrs_data_provider(sys.argv[1]).get_device_version().name)
    """

            try:
                # Run the script using the helper function
                stdout, stderr, returncode = await run_subprocess_with_logging(
                    sys.executable,
                    "-c",
                    script,
                    str(self._recording.path.as_posix()),
                    logger_instance=logger,
                )

                if returncode != 0:
                    logger.error(f"Failed to get device version: {stderr.decode()}")
                    return MpsAriaDevice.UNKNOWN

                device_type_str = stdout.decode().strip()
                logger.debug(f"Device type: {device_type_str}")
                if device_type_str == "Gen1":
                    return MpsAriaDevice.ARIA_GEN1
                elif device_type_str == "Gen2":
                    return MpsAriaDevice.ARIA_GEN2
                elif device_type_str == "NotValid":
                    return MpsAriaDevice.UNKNOWN
                return MpsAriaDevice[device_type_str]
            except Exception as e:
                logger.error(
                    f"Failed to get device version from {self._recording.path}: {e}"
                )
                return MpsAriaDevice.UNKNOWN
