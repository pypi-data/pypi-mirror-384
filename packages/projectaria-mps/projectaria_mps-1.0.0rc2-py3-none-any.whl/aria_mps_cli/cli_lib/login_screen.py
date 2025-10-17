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

from aria_mps_cli.cli_lib.authentication import AuthenticationError

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Grid
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


logger = logging.getLogger(__name__)


class LoginScreen(ModalScreen[bool]):
    """Login screen"""

    CSS: str = """
    LoginScreen {
        align: center middle;
        background: $background 100%;
    }


    #dialog {
        grid-size: 2 5;
        grid-gutter: 1 2;
        grid-rows: 2 3 3 4 1;
        padding: 1 1 0 1;
        width: 68;
        height: 21;
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

    #login_error {
        column-span: 2;
        text-align: center;
    }
    """

    def __init__(self, username: str) -> None:
        self._username: str = username
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        self._login_attempt: int = 1

        yield Grid(
            Static("[b]Log in to Aria Machine Perception Services", id="title"),
            Input(value=self._username, id="username", disabled=True),
            Input(placeholder="Password", id="password", password=True),
            Button("Cancel", variant="default", id="cancel"),
            Button("Log in", variant="primary", id="login"),
            Static(id="login_error"),
            id="dialog",
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle Enter key press in the password input field.
        """
        if event.input.id == "password":
            login_button = self.query_one("#login", Button)
            login_button.press()

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
            self.dismiss(False)
            return
        elif event.button.id == "login":
            await self._handle_login()

    async def _handle_login(self) -> None:
        """
        Handle the login action.
        """
        username = self.query_one("#username", Input).value.strip()
        password = self.query_one("#password", Input).value.strip()
        if username and password:
            try:
                login_button = self.query_one("#login", Button)
                login_button.disabled = True
                await self.app._authenticator.password_login(
                    username, password, save_token=True
                )
                self.dismiss(True)
            except AuthenticationError as e:
                logger.exception(e)
                login_button.disabled = False
                if self._login_attempt < 3:
                    self.query_one("#login_error").update(
                        Text.from_markup(
                            f"[red][i]Log in attempt failed. [/][b][i]{3 - self._login_attempt }/3 attempts left."
                        )
                    )
                    self._login_attempt += 1
                else:
                    self.dismiss(False)
        else:
            if self._login_attempt < 3:
                self.query_one("#login_error").update(
                    Text.from_markup(
                        f"[red][i]Username or password cannot be empty. [/][b][i]{3 - self._login_attempt }/3 attempts left."
                    )
                )
                self._login_attempt += 1
            else:
                self.dismiss(False)
