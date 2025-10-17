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
import io
import logging
import os
from typing import Optional

import pyperclip
import qrcode

from aria_mps_cli.cli_lib.authentication import AuthenticationError

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static


logger = logging.getLogger(__name__)


def _is_ssh_session() -> bool:
    """
    Detect if running in an SSH session.

    Returns:
        True if in SSH session, False otherwise
    """
    return bool(
        os.environ.get("SSH_CONNECTION")
        or os.environ.get("SSH_CLIENT")
        or os.environ.get("SSH_TTY")
    )


# Device flow dictionary keys
_KEY_USER_CODE = "user_code"
_KEY_DEVICE_CODE = "device_code"
_KEY_EXPIRES_IN = "expires_in"

# Default timeout for device flow code expiration (in seconds)
_DEFAULT_EXPIRES_IN_SECS = 300  # 5 minutes


class MMAScreen(ModalScreen[bool]):
    """MMA authentication screen that displays a link and code for user login"""

    CSS: str = """
    MMAScreen {
        align: center middle;
        background: $background 100%;
    }

    #dialog {
        grid-size: 2 7;
        grid-gutter: 1 1;
        grid-rows: 4 7 21 1 3 1 3;
        padding: 2 2 2 2;
        width: 98;
        height: 53;
        border: thick $background 100%;
        background: $surface;
    }

    .centered-content {
        column-span: 2;
        text-align: center;
        margin: 0 2;
    }

    #title {
        column-span: 2;
        content-align: center top;
        color: $accent;
        text-align: center;
        height: auto;
        padding: 0;
        margin-bottom: 2;
    }

    #subtitle {
        color: $accent;
        margin-top: 0;
        padding-top: 0;
    }

    #qr_code {
        text-align: center;
        background: $surface;
        width: 100%;
        height: auto;
        min-height: 25;
        content-align: center top;
        margin-top: -2;
        margin-bottom: 2;
        padding-bottom: 2;
    }

    #code_container {
        column-span: 2;
        align: center middle;
        height: auto;
        min-height: 3;
    }

    #code {
        width: auto;
        height: auto;
        min-height: 3;
        text-align: center;
        content-align: center middle;
        padding: 1;
    }

    #copy_code {
        width: auto;
        min-width: 3;
        height: 3;
        padding: 0 1;
    }


    #cancel_container {
        column-span: 2;
        width: 100%;
        height: auto;
        align-horizontal: center;
    }

    #cancel {
        width: 50%;
        height: auto;
        text-align: center;
    }
    """

    def __init__(
        self,
        user_code: str = "",
        device_code: str = "",
        login_url: str = "https://work.meta.com/cli",
        expires_in: int = _DEFAULT_EXPIRES_IN_SECS,
        polling_interval: int = 5,
    ) -> None:
        super().__init__()
        self._user_code = user_code
        self._device_code = device_code
        self._login_url = login_url
        self._expires_in_secs = expires_in
        self._polling_interval = polling_interval
        self._is_cancelled = False
        self._polling_task: Optional[asyncio.Task] = None

    @staticmethod
    def _generate_qr_code_ascii(url: str) -> str:
        """
        Generate ASCII representation of QR code for the given URL.

        Args:
            url: The URL to encode in the QR code

        Returns:
            ASCII art representation of the QR code
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        output = io.StringIO()
        qr.print_ascii(out=output, invert=True)
        return output.getvalue()

    @staticmethod
    def _format_user_code(user_code: str) -> str:
        """
        Format user code with spaces between characters for better readability.

        Args:
            user_code: The user code to format

        Returns:
            Formatted code string (e.g., "A B C D E F G H")
        """
        return " ".join(user_code) if user_code else ""

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        qr_code = self._generate_qr_code_ascii(self._login_url)
        is_ssh = _is_ssh_session()

        # Build code container widgets
        code_container_widgets = [
            Static(
                Text.from_markup(
                    f"[b bright_yellow]{self._format_user_code(self._user_code)}[/]"
                    if self._user_code
                    else "[b bright_yellow]Loading...[/]"
                ),
                id="code",
            )
        ]

        # Add copy button only if not in SSH session
        if not is_ssh:
            code_container_widgets.append(
                Button(
                    "📋",
                    variant="default",
                    id="copy_code",
                    tooltip="Copy code to clipboard",
                )
            )
        yield Grid(
            Static(
                "[b]Authentication Required[/b]\nPlease complete authentication by:",
                id="title",
            ),
            Static(
                Text.from_markup(
                    f"1. Visit [link={self._login_url}][blue]{self._login_url}[/blue][/link]\n\nor\n\nscan the QR code:\n"
                ),
                id="step1",
                classes="centered-content",
            ),
            Static(qr_code, id="qr_code", classes="centered-content"),
            Static(
                "2. Enter the code:",
                id="step2",
                classes="centered-content",
            ),
            Horizontal(
                *code_container_widgets,
                id="code_container",
                classes="centered-content",
            ),
            Static(
                Text.from_markup("[dim]Code expires in: 10:00[/dim]"),
                id="timer",
                classes="centered-content",
            ),
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                id="cancel_container",
                classes="centered-content",
            ),
            id="dialog",
        )

    async def on_mount(self) -> None:
        """Start polling when screen is mounted and set focus on cancel button."""
        # Generate device flow if code is empty
        if not self._user_code:
            logger.info("Generating initial device flow...")
            device_flow_info = await self.app._authenticator.get_mma_device_flow_info()
            self._user_code = device_flow_info[_KEY_USER_CODE]
            self._device_code = device_flow_info[_KEY_DEVICE_CODE]
            self._expires_in_secs = device_flow_info.get(
                _KEY_EXPIRES_IN, _DEFAULT_EXPIRES_IN_SECS
            )
            # Note: Keep the original login_url from __init__, don't overwrite

            # Update UI with generated code only
            self.query_one("#code").update(
                Text.from_markup(
                    f"[b bright_yellow]{self._format_user_code(self._user_code)}[/]"
                )
            )

        self._polling_task = asyncio.create_task(self._poll_for_completion())
        # Set focus on cancel button by default
        cancel_button = self.query_one("#cancel", Button)
        cancel_button.focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "cancel":
            self._is_cancelled = True
            if self._polling_task:
                self._polling_task.cancel()
            self.dismiss(False)
        elif event.button.id == "copy_code" and not _is_ssh_session():
            await self._copy_code()

    async def on_key(self, event) -> None:
        """Handle key press events."""
        if event.key == "escape":
            cancel_button = self.query_one("#cancel", Button)
            cancel_button.press()

    def _format_time_remaining(self, seconds: float) -> str:
        """
        Format remaining time as MM:SS.

        Args:
            seconds: Remaining seconds

        Returns:
            Formatted time string (e.g., "9:45")
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    async def _poll_for_completion(self) -> None:
        """
        Poll the authentication endpoint periodically to check if login is completed.
        Timer updates every second, but authentication polling happens at polling_interval.
        """
        start_time = asyncio.get_event_loop().time()
        last_timer_update = 0.0
        last_auth_check = 0.0

        while not self._is_cancelled:
            try:
                current_time = asyncio.get_event_loop().time()
                elapsed_time = current_time - start_time
                remaining_time = self._expires_in_secs - elapsed_time

                # Update timer every second
                if current_time - last_timer_update >= 1.0:
                    if remaining_time > 0:
                        time_str = self._format_time_remaining(remaining_time)
                        self.query_one("#timer").update(
                            Text.from_markup(f"[dim]Code expires in: {time_str}[/dim]")
                        )
                        last_timer_update = current_time

                # Check if the code has expired
                if elapsed_time >= self._expires_in_secs:
                    logger.info("Authentication code expired, generating new code...")
                    self.query_one("#timer").update(
                        Text.from_markup("[dim]Refreshing code...[/dim]")
                    )
                    await self._refresh_code()
                    return

                # Check authentication status at polling interval
                if current_time - last_auth_check >= self._polling_interval:
                    if await self._check_authentication_status():
                        return
                    last_auth_check = current_time

                # Wait for 1 second before next iteration (for timer updates)
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.debug("Polling task cancelled")
                return
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                await asyncio.sleep(self._polling_interval)

    async def _check_authentication_status(self) -> bool:
        """
        Check if the authentication has been completed.

        Returns:
            True if authentication is complete, False otherwise
        """
        try:
            logger.debug("Checking authentication status...")

            # Poll for auth code using device code (step 3 of MMA flow)
            auth_code = await self.app._authenticator.check_mma_device_authorization(
                self._device_code
            )

            if auth_code:
                logger.debug("Got auth code, getting access token...")

                # Get access token using auth code (step 4 of MMA flow)
                access_token = await self.app._authenticator.get_mma_access_token(
                    auth_code
                )

                # Set the access token in the authenticator
                await self.app._authenticator.set_auth_token(
                    access_token, save_token=True
                )

                logger.info("Authentication successful!")
                self.dismiss(True)
                return True
            else:
                logger.debug("Still waiting for authentication...")
                return False

        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking authentication: {e}")
            return False

    async def _copy_code(self) -> None:
        """
        Copy the authentication code to clipboard.
        """
        try:
            if self._user_code:
                pyperclip.copy(self._user_code)
                logger.info("Code copied to clipboard")

                # Show success notification
                self.app.notify(
                    "✓ Code copied to clipboard", severity="information", timeout=2
                )
        except Exception as e:
            logger.error(f"Failed to copy code: {e}")
            # Show error notification
            self.app.notify("✗ Failed to copy code", severity="error", timeout=2)

    async def _refresh_code(self) -> None:
        """
        Refresh the authentication code by getting a new device flow.
        """
        try:
            logger.info("Refreshing authentication code...")

            # Cancel existing polling task
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass

            # Get new device flow info
            device_flow_info = await self.app._authenticator.get_mma_device_flow_info()
            self._user_code = device_flow_info[_KEY_USER_CODE]
            self._device_code = device_flow_info[_KEY_DEVICE_CODE]
            self._expires_in_secs = device_flow_info.get(
                _KEY_EXPIRES_IN, _DEFAULT_EXPIRES_IN_SECS
            )
            # Note: Keep the original login_url, don't update it from device_flow_info

            # Update UI with new code only (QR code and URL stay the same)
            self.query_one("#code").update(
                Text.from_markup(
                    f"[b bright_yellow]{self._format_user_code(self._user_code)}[/]"
                )
            )

            # Reset timer
            self.query_one("#timer").update(
                Text.from_markup("[dim]Code expires in: 10:00[/dim]")
            )

            # Start new polling task
            self._is_cancelled = False
            self._polling_task = asyncio.create_task(self._poll_for_completion())

            logger.info("Authentication code refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh code: {e}")

    def on_unmount(self) -> None:
        """Clean up when the screen is unmounted."""
        if self._polling_task:
            self._polling_task.cancel()
