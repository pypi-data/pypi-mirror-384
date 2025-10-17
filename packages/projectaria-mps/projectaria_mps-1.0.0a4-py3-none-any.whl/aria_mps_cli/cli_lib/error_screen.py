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

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ErrorScreen(ModalScreen[None]):
    """Error message modal screen"""

    CSS: str = """
    ErrorScreen {
        align: center middle;
        background: $background 80%;
    }

    #dialog {
        grid-size: 1;
        grid-gutter: 1 2;
        grid-rows: 1 auto 5;
        padding: 1 2;
        width: 60;
        max-height: 30;
        border: thick $error;
        background: $surface;
    }

    #title {
        content-align: center middle;
        color: $error;
        text-style: bold;
        text-align: center;
    }

    #error_message {
        padding: 1 0;
        overflow-y: auto;
        max-height: 15;
    }

    Button {
        width: 100%;
        height: auto;
        text-align: center;
        margin: 0 2;
    }
    """

    def __init__(self, error_message: str) -> None:
        """Initialize error screen with message.

        Args:
            error_message: The error message to display
        """
        self._error_message = error_message
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Grid(
            Static("[b red]Error", id="title"),
            Static(self._error_message, id="error_message"),
            Button("OK", variant="primary", id="ok"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "ok":
            self.dismiss()
