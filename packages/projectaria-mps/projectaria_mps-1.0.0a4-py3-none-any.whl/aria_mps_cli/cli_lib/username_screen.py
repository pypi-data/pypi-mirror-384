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

import logging

from aria_mps_cli.cli_lib.authentication import AuthenticationError, LoginMethod
from aria_mps_cli.cli_lib.error_screen import ErrorScreen
from aria_mps_cli.cli_lib.login_screen import LoginScreen
from aria_mps_cli.cli_lib.mma_screen import MMAScreen

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Grid
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


logger = logging.getLogger(__name__)


class UsernameScreen(ModalScreen[bool]):
    """Username validation screen to determine appropriate login method"""

    CSS: str = """
    UsernameScreen {
        align: center middle;
        background: $background 100%;
    }

    #dialog {
        grid-size: 2 4;
        grid-gutter: 1 2;
        grid-rows: 2 3 4 1;
        padding: 1 1 0 1;
        width: 68;
        height: 18;
        border: thick $background 100%;
        background: $surface;
    }

    #title {
        column-span: 2;
        content-align: center middle;
    }

    Input {
        column-span: 2;
        margin: 0 4;
    }

    Button {
        width: 100%;
        height: auto;
        text-align: center;
        margin: 0 2;
    }

    #username_error {
        column-span: 2;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        self._validation_attempt: int = 1

        yield Grid(
            Static(
                "[b]Enter Username for Aria Machine Perception Services", id="title"
            ),
            Input(placeholder="Username", id="username"),
            Button("Cancel", variant="default", id="cancel"),
            Button("Continue", variant="primary", id="continue"),
            Static(id="username_error"),
            id="dialog",
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle Enter key press in the username input field.
        """
        if event.input.id == "username":
            continue_button = self.query_one("#continue", Button)
            continue_button.press()

    async def on_key(self, event: Key) -> None:
        """
        Handle key press events.
        """
        if event.key == "escape":
            cancel_button = self.query_one("#cancel", Button)
            cancel_button.press()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.
        """
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        elif event.button.id == "continue":
            await self._handle_continue()

    async def _handle_continue(self) -> None:
        """
        Handle the continue action (either from button or Enter key).
        """
        username = self.query_one("#username", Input).value.strip()
        logger.debug(f">Validating username: {username}")

        if username:

            def __login_callback(success: bool) -> None:
                if success:
                    self.dismiss(True)

            try:
                # Disable the continue button during validation
                continue_button = self.query_one("#continue", Button)
                continue_button.disabled = True

                # Validate username and determine login method
                login_method = await self._validate_username_and_get_login_method(
                    username
                )

                if login_method == LoginMethod.PASSWORD:
                    self.app.push_screen(
                        LoginScreen(username=username), __login_callback
                    )
                elif login_method == LoginMethod.MMA:
                    # Initiate MMA device flow and show authentication screen
                    self.app.push_screen(MMAScreen(), __login_callback)
            except AuthenticationError as e:
                logger.exception(e)
                # Show error modal with the exception message
                self.app.push_screen(ErrorScreen(str(e)))
            finally:
                continue_button.disabled = False
        else:
            self.query_one("#username_error", Static).update(
                Text("Username cannot be empty", style="red")
            )
            self._validation_attempt += 1
            if self._validation_attempt > 3:
                self.dismiss(None)
                return

    async def _validate_username_and_get_login_method(
        self, username: str
    ) -> LoginMethod:
        """
        Validate the username and determine the appropriate login method.

        Args:
            username: The username to validate

        Returns:
            LoginMethod: The login method to use (MMA, PASSWORD, or UNKNOWN)

        Raises:
            AuthenticationError: If username validation fails
        """
        try:
            login_method = await self.app._authenticator.validate_username(username)
            return login_method
        except Exception as e:
            raise AuthenticationError(f"Failed to validate username: {str(e)}")
