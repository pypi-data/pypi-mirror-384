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

import argparse
import asyncio
import glob
import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Union

from aria_mps_cli.cli_lib.http_helper import HttpHelper
from aria_mps_cli.cli_lib.multi_recording_mps import MultiRecordingMps
from aria_mps_cli.cli_lib.multi_recording_request import MultiRecordingRequest
from aria_mps_cli.cli_lib.request_monitor import RequestMonitor
from aria_mps_cli.cli_lib.single_recording_mps import SingleRecordingMps
from aria_mps_cli.cli_lib.single_recording_request import SingleRecordingRequest
from aria_mps_cli.cli_lib.types import (
    ModelState,
    MpsAriaDevice,
    MpsFeature,
    MpsRequestSource,
)

logger = logging.getLogger(__name__)

_SINGLE_COMMAND: str = "single"
_MULTI_COMMAND: str = "multi"


class Mps:
    """MPS main class"""

    def __init__(self, http_helper: HttpHelper):
        self._http_helper: HttpHelper = http_helper
        self._features: List[MpsFeature] = []
        self._requestor = None
        self._requests: Union[Set[SingleRecordingMps], Set[MultiRecordingMps]] = {}

    async def run(self, args: argparse.Namespace) -> None:
        """
        The core MPS functionality
        """
        logger.debug("Running MPS")
        # Create MPS Request Monitor and MPS Requestor
        self._features = (
            list(args.features)
            if args.mode == _SINGLE_COMMAND
            else [MpsFeature.MULTI_SLAM]
        )
        recordings: Set[Path] = set()
        for input_path in args.input:
            if input_path.is_file():
                if input_path.suffix != ".vrs":
                    raise ValueError(f"Only .vrs file supported: {input_path}")
                recordings.add(input_path)
            elif input_path.is_dir():
                for rec in glob.glob(f"{input_path}/**/*.vrs", recursive=True):
                    recordings.add(Path(rec))
            else:
                logger.error(f"Invalid input path: {input_path}")

        if len(recordings) == 0:
            raise ValueError("No valid input recordings found")

        self._request_monitor = RequestMonitor(self._http_helper)
        common_args: Dict[str, Any] = {
            "http_helper": self._http_helper,
            "force": args.force,
            "retry_failed": args.retry_failed,
            "suffix": args.suffix,
            "persist_on_failure": args.persist_on_failure,
        }
        if args.mode == _MULTI_COMMAND:
            self._requestor: MultiRecordingRequest = MultiRecordingRequest(
                http_helper=self._http_helper,
            )
            # Add new VRS files to be processed
            self._requests = {
                MultiRecordingMps(
                    recordings=recordings,
                    output_dir=args.output_dir,
                    requestor=self._requestor,
                    request_monitor=self._request_monitor,
                    name=args.name,
                    source=MpsRequestSource.MPS_CLI,
                    **common_args,
                )
            }
        elif args.mode == _SINGLE_COMMAND:
            self._requestor: SingleRecordingRequest = SingleRecordingRequest(
                http_helper=self._http_helper,
            )

            self._requests = {
                SingleRecordingMps(
                    recording=rec,
                    features=args.features,
                    requestor=self._requestor,
                    request_monitor=self._request_monitor,
                    source=MpsRequestSource.MPS_CLI,
                    **common_args,
                )
                for rec in recordings
            }
            logger.debug(
                f"Added {len(recordings)} recordings for Single MPS processing"
            )

        else:
            raise ValueError(f"Unknown mode {args.mode}")

        logger.debug(f"Waiting for {len(self._requests)} requests to finish")
        # Wait for all requests to finish
        await asyncio.gather(
            *[asyncio.create_task(request.run()) for request in self._requests]
        )
        logger.debug("All MPS requests finished")

    def get_status(self) -> Mapping[Path, Dict[MpsFeature, ModelState]]:
        """
        Refresh the status of all recordings
        """
        current_states: Mapping[Path, Dict[MpsFeature, ModelState]] = {}
        for request in self._requests:
            if isinstance(request, SingleRecordingMps):
                current_states[request.recording] = {}
                for feature in self._features:
                    current_states[request.recording][feature] = request.get_status(
                        feature
                    )
            else:
                for rec in request.recordings:
                    current_states[rec] = {}
                    current_states[rec][self._features[0]] = request.get_status(rec)

        return current_states

    def get_device_type(self, recording_path: Path) -> Optional[MpsAriaDevice]:
        """
        Get device type for a recording by path with caching
        """

        # If not in cache, look through requests
        for request in self._requests:
            if isinstance(request, SingleRecordingMps):
                if request.recording == recording_path:
                    return request.get_device_type()
            elif isinstance(request, MultiRecordingMps):
                return request.get_device_type(recording_path)
        return None

    @property
    def features(self):
        return self._features
