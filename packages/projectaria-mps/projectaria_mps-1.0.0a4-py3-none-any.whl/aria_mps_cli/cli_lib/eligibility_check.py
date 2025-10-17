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
from abc import ABC, abstractmethod
from typing import Any, Dict, Final, List, Optional

from aria_mps_cli.cli_lib.constants import (
    ErrorCode,
    KEY_VHC_ARIA_GEN1_DEFAULT,
    KEY_VHC_ARIA_GEN2_DEFAULT,
)
from aria_mps_cli.cli_lib.types import AriaRecording, MpsAriaDevice, MpsFeature

logger = logging.getLogger(__name__)


def validate_recording_eligibility(
    recording: AriaRecording,
    feature: MpsFeature,
) -> Optional[ErrorCode]:
    """
    Validates recording eligibility by determining device type and checking feature compatibility.

    Args:
        recording: The AriaRecording to validate
        feature: The MpsFeature to check eligibility for

    Returns:
        ErrorCode if validation fails, None if successful
    """

    if recording.device_type is None:
        logger.error(f"Failed to determine device type for {recording.path}")
        return ErrorCode.HEALTH_CHECK_FAILURE

    logger.info(f"Device type: {recording.device_type}")
    if recording.device_type is MpsAriaDevice.ARIA_GEN1:
        eligibility_checker = EligibilityCheckerGen1(recording)
    elif recording.device_type is MpsAriaDevice.ARIA_GEN2:
        eligibility_checker = EligibilityCheckerGen2(recording)
    else:
        logger.error(
            f"Failed to determine device type for {recording.path}. device_type={recording.device_type}"
        )
        return ErrorCode.DEVICE_TYPE_UNSUPPORTED

    error_code: Optional[ErrorCode] = eligibility_checker.check_eligibility_error(
        feature
    )
    if error_code:
        logger.error(f"VrsHealthCheck failed for {recording.path}")
    return error_code


class EligibilityChecker(ABC):
    """
    Base class for checking if a recording is eligible for processing with a given MPS feature.
    """

    VHC_KEY_SECTION_LOCATION: str = ""
    VHC_KEY_SECTION_DEFAULT: str = ""

    _VHC_KEY_FINAL_RESULT: Final[str] = "final_result"
    _VHC_KEY_FAILED_CHECKS: Final[str] = "failed_checks"
    _VHC_KEY_WARN_CHECKS: Final[str] = "warn_checks"
    _VHC_KEY_STREAM_CHECKS: Final[str] = "performed_checks_with_details"

    _VHC_OUT_PASS: Final[str] = "pass"
    _VHC_OUT_WARN: Final[str] = "warn"
    _VHC_OUT_FAIL: Final[str] = "fail"

    def __init__(self, recording: AriaRecording) -> None:
        self._recording: AriaRecording = recording

    @abstractmethod
    def check_eligibility_error(self, feature: MpsFeature) -> Optional[ErrorCode]:
        """
        Checks if an Aria Recording is eligible for processing with selected MPS feature
        based on the results of the VRS Health Check.

        Args:
            feature (MpsFeature): The MPS feature to check eligibility for.
        Returns:
            None if the recording is eligible for processing with the selected feature, an error code otherwise.
        """
        raise NotImplementedError()


class EligibilityCheckerGen1(EligibilityChecker):
    """
    Check if an Aria gen1 recording is eligible for processing with a given MPS feature.
    """

    VHC_KEY_SECTION_LOCATION: Final[str] = "AriaGen1_Location"
    VHC_KEY_SECTION_DEFAULT: Final[str] = KEY_VHC_ARIA_GEN1_DEFAULT

    def check_eligibility_error(self, feature: MpsFeature) -> Optional[ErrorCode]:
        """
        Checks if an Aria Recording is eligible for processing with selected MPS feature
        based on the results of the VRS Health Check.

        Args:
            feature (MpsFeature): The MPS feature to check eligibility for.
        Returns:
            None if the recording is eligible for processing with the selected feature, an error code otherwise.
        """
        if not self._recording.health_check_path.exists():
            raise FileNotFoundError(f"No health check found for {self._recording.path}")

        with open(self._recording.health_check_path) as vhc:
            vhc_json: Dict[str, Any] = json.load(vhc)

        if feature in [MpsFeature.SLAM, MpsFeature.MULTI_SLAM]:
            location_status: Optional[str] = vhc_json.get(
                self.VHC_KEY_SECTION_LOCATION, {}
            ).get(self._VHC_KEY_FINAL_RESULT)
            if not location_status:
                logger.error("Unable to determine location status from VHC output")
            return (
                ErrorCode.HEALTH_CHECK_FAILURE
                if location_status == self._VHC_OUT_FAIL or location_status is None
                else None
            )

        section: Dict[str, Any] = vhc_json[self.VHC_KEY_SECTION_DEFAULT]
        if feature == MpsFeature.EYE_GAZE:
            return (
                ErrorCode.HEALTH_CHECK_FAILURE
                if not self._is_eligible_stream(section, "Eye Camera Class #1")
                else None
            )
        elif feature == MpsFeature.HAND_TRACKING:
            return (
                ErrorCode.HEALTH_CHECK_FAILURE
                if any(
                    not self._is_eligible_stream(section, f"Camera Data (SLAM) #{i}")
                    for i in range(1, 2)
                )
                else None
            )

        raise NotImplementedError(f"Unknown feature type {feature}")

    def _is_eligible_stream(self, section_json: Dict[str, Any], stream: str) -> bool:
        """
        Check if the Aria Recording's stream is eligible for MPS processing.

        Args:
            section_json (Dict[str, Any]): The selected section of JSON output of the VRS Health Check.
            stream (str): The stream to check eligibility for.
        Returns:
            True if the Aria Recording's stream is eligible for MPS processing, False otherwise.
        """

        has_stream: bool = stream in section_json[self._VHC_KEY_STREAM_CHECKS]
        if not has_stream:
            return False

        errors: List[str] = [
            check
            for check in section_json[self._VHC_KEY_FAILED_CHECKS]
            if check.startswith(stream)
        ]
        if errors:
            logger.debug(f"Failed checks: {errors}")
            return False

        warnings: List[str] = [
            check
            for check in section_json[self._VHC_KEY_WARN_CHECKS]
            if check.startswith(stream)
        ]
        if warnings:
            logger.debug(f"Warning checks: {warnings}")

        return True


class EligibilityCheckerGen2(EligibilityChecker):
    """
    Check if an Aria gen2 recording is eligible for processing with a given MPS feature.
    """

    VHC_KEY_SECTION_LOCATION: Final[str] = "AriaGen2_Location"
    VHC_KEY_SECTION_DEFAULT: Final[str] = KEY_VHC_ARIA_GEN2_DEFAULT

    def check_eligibility_error(self, feature: MpsFeature) -> Optional[ErrorCode]:
        """
        Checks if an Aria Recording is eligible for processing with selected MPS feature
        based on the results of the VRS Health Check.

        Args:
            feature (MpsFeature): The MPS feature to check eligibility for.
        Returns:
            None if the recording is eligible for processing with the selected feature, an error code otherwise.
        """
        if not self._recording.health_check_path.exists():
            raise FileNotFoundError(f"No health check found for {self._recording.path}")

        if feature in [
            MpsFeature.EYE_GAZE,
            MpsFeature.HAND_TRACKING,
            MpsFeature.MULTI_SLAM,
        ]:
            # requestor should reject the Recording in a previous step
            return ErrorCode.DEVICE_TYPE_UNSUPPORTED

        with open(self._recording.health_check_path) as vhc:
            vhc_json: Dict[str, Any] = json.load(vhc)

        if feature == MpsFeature.SLAM:
            location_status: Optional[str] = vhc_json.get(
                self.VHC_KEY_SECTION_LOCATION, {}
            ).get(self._VHC_KEY_FINAL_RESULT)
            if not location_status:
                logger.error("Unable to determine location status from VHC output")
            return (
                ErrorCode.HEALTH_CHECK_FAILURE
                if location_status == self._VHC_OUT_FAIL or location_status is None
                else None
            )

        raise NotImplementedError(f"Unknown feature type {feature}")
