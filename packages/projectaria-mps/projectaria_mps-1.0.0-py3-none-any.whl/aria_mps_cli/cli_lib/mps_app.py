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
import logging
from pathlib import Path
from time import monotonic
from typing import Any, Dict, Mapping, Optional

import aiofiles

from aria_mps_cli.cli_lib.authentication import Authenticator
from aria_mps_cli.cli_lib.common import get_pretty_size
from aria_mps_cli.cli_lib.constants import DisplayStatus
from aria_mps_cli.cli_lib.http_helper import HttpHelper
from aria_mps_cli.cli_lib.mps import Mps
from aria_mps_cli.cli_lib.quit_screen import QuitMode, QuitScreen
from aria_mps_cli.cli_lib.types import ModelState, MpsAriaDevice, MpsFeature
from aria_mps_cli.cli_lib.username_screen import UsernameScreen

from rich import box
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Footer, Header, Rule, Static

logger = logging.getLogger(__name__)
from_markup = Text.from_markup


class ElapsedTime(Static):
    """
    A static widget that displays elapsed time since start
    """

    elapsed_time = reactive(0)

    def reset(self) -> None:
        """
        Reset the timer
        """
        self._start_time = monotonic()

    def on_mount(self) -> None:
        """
        Called when the widget is mounted
        """
        self._start_time = monotonic()
        self.set_interval(1, self.update_elapsed_time)

    def update_elapsed_time(self) -> None:
        """
        Update the elapsed time
        """
        self.elapsed_time = monotonic() - self._start_time

    def watch_elapsed_time(self) -> None:
        """
        Update the UI when elapsed time is updated
        """
        self.update(
            f"{Text.from_markup(':clock1:')} Time elapsed: [bold][cyan]{self._get_pretty_time()}"
        )

    def _get_pretty_time(self) -> str:
        """
        Convert time delta to human readable format
        """
        seconds = int(self.elapsed_time)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{days}d:{hours}h:{minutes}m:{seconds}s"
        return f"{hours}h:{minutes}m:{seconds}s"


class SummaryStats(Static):
    """
    A static widget that displays summary statistics of all recordings
    """

    mps_status: Mapping[Path, Dict[MpsFeature, ModelState]] = reactive({})

    def __init__(self, mps: Mps) -> None:
        self._mps: Mps = mps
        super().__init__()

    def on_mount(self) -> None:
        """Called when the widget is mounted"""
        self.set_interval(1 / 2, self.update_status)

    def update_status(self) -> None:
        """Get latest status from MPS"""
        self.mps_status = self._mps.get_status()

    def watch_mps_status(self) -> None:
        """Update the summary stats display"""
        if not self.mps_status:
            return

        num_recordings = len(self.mps_status)
        total_requests = 0
        completed = 0
        failed = 0
        in_progress = 0

        # Count feature requests
        for recording_statuses in self.mps_status.values():
            for state in recording_statuses.values():
                total_requests += 1
                if state.status == DisplayStatus.SUCCESS:
                    completed += 1
                elif state.status == DisplayStatus.ERROR:
                    failed += 1
                elif state.status not in [DisplayStatus.SUCCESS, DisplayStatus.ERROR]:
                    in_progress += 1

        summary = Text()
        summary.append("📊 Summary: ", style="bold")
        summary.append(f"Recordings: {num_recordings} | ", style="cyan")
        summary.append(f"Total Requests: {total_requests} | ", style="cyan")
        summary.append(f"✓ Success: {completed} | ", style="green")
        summary.append(f"✗ Failed: {failed} | ", style="red")
        summary.append(f"⟳ In Progress: {in_progress}", style="yellow")

        self.update(summary)


class StatusTable(Static):
    """
    A static widget that displays status of all recordings
    """

    mps_status: Mapping[Path, Dict[MpsFeature, ModelState]] = reactive({})
    filter_mode: str = reactive("all")  # "all", "failed", "success", "in_progress"
    sort_by: str = reactive(
        "name_asc"
    )  # "name_asc", "name_desc", "status", "size_asc", "size_desc"

    def __init__(self, mps: Mps) -> None:
        self._mps: Mps = mps
        self._file_sizes: Dict[Path, int] = {}
        self._table: Optional[Table] = None
        super().__init__()

    def on_mount(self) -> None:
        """
        Called when the widget is mounted
        """
        self.set_interval(1 / 2, self.update_status)
        self.set_interval(1 / 5, self.refresh_ui)

    def refresh_ui(self) -> None:
        """
        Refresh the UI
        """
        if self._table:
            self.update(self._table)

    def update_status(self) -> None:
        """
        Get latest status from MPS
        """
        self.mps_status = self._mps.get_status()

    def set_filter(self, filter_mode: str) -> None:
        """Set the filter mode"""
        self.filter_mode = filter_mode
        # Force table rebuild by calling watch_mps_status directly
        if self.mps_status:
            self.run_worker(self.watch_mps_status)

    def set_sort(self, sort_by: str) -> None:
        """Set the sort mode"""
        self.sort_by = sort_by
        # Force table rebuild by calling watch_mps_status directly
        if self.mps_status:
            self.run_worker(self.watch_mps_status)

    async def _get_file_size(self, vrs_path: Path) -> int:
        """
        Get file size of given VRS file
        """
        if vrs_path not in self._file_sizes:
            self._file_sizes[vrs_path] = (await aiofiles.os.stat(vrs_path)).st_size
        return self._file_sizes[vrs_path]

    def _should_include_recording(
        self, vrs_path: Path, feature_status: Dict[MpsFeature, ModelState]
    ) -> bool:
        """
        Check if recording should be included based on filters.

        Filter behavior:
        - "all": Show everything (no filtering)
        - "failed": Show if ANY feature failed (lenient)
        - "success": Show only if ALL features succeeded (strict)
        - "in_progress": Show if ANY feature is still processing (lenient)
        """
        # Apply status filter
        if self.filter_mode == "all":
            return True

        statuses = [state.status for state in feature_status.values()]
        if self.filter_mode == "failed":
            # Show if at least one feature failed
            return DisplayStatus.ERROR in statuses
        elif self.filter_mode == "success":
            # Show only if ALL features are successful (strict)
            return all(s == DisplayStatus.SUCCESS for s in statuses)
        elif self.filter_mode == "in_progress":
            # Show if at least one feature is still processing
            return any(
                s not in [DisplayStatus.SUCCESS, DisplayStatus.ERROR] for s in statuses
            )
        return True

    async def watch_mps_status(self) -> None:
        """
        Update the table on status update
        """
        all_vrs_paths = list(self.mps_status.keys())
        if not all_vrs_paths:
            return

        # Apply filtering
        filtered_paths = [
            path
            for path in all_vrs_paths
            if self._should_include_recording(path, self.mps_status[path])
        ]

        # Apply sorting
        if self.sort_by in ["name_asc", "name_desc"]:
            # Sort by name (ascending or descending based on sort_by)
            reverse_order = self.sort_by == "name_desc"
            vrs_paths = sorted(filtered_paths, reverse=reverse_order)
        elif self.sort_by == "status":
            # Sort by status (errors first, then in-progress, then success)
            def status_sort_key(path):
                statuses = [s.status for s in self.mps_status[path].values()]
                if DisplayStatus.ERROR in statuses:
                    return 0
                elif any(
                    s not in [DisplayStatus.SUCCESS, DisplayStatus.ERROR]
                    for s in statuses
                ):
                    return 1
                return 2

            vrs_paths = sorted(filtered_paths, key=status_sort_key)
        elif self.sort_by in ["size_asc", "size_desc"]:
            # Sort by file size
            # We need to gather all sizes first, then sort
            path_sizes = []
            for path in filtered_paths:
                size = await self._get_file_size(path)
                path_sizes.append((path, size))

            # Sort by size (ascending or descending based on sort_by)
            reverse_order = self.sort_by == "size_desc"
            path_sizes.sort(key=lambda x: x[1], reverse=reverse_order)
            vrs_paths = [path for path, _ in path_sizes]
        else:
            vrs_paths = filtered_paths

        # Build table
        table = Table(
            expand=True,
            box=box.SQUARE_DOUBLE_HEAD,
            style="grey37",
            header_style="bold bright_cyan",
        )
        table.add_column("ID", style="cyan")
        table.add_column("RECORDING", overflow="fold")
        table.add_column("FILE SIZE", justify="right")
        table.add_column("DEVICE")
        for feature in self._mps.features:
            table.add_column(feature.value.upper())

        if not vrs_paths:
            table.add_row(
                "-",
                "[yellow]No recordings match the current filter",
                "-",
                "-",
                *["-" for _ in self._mps.features],
            )
        else:
            for i, vrs_path in enumerate(vrs_paths, 1):
                feature_status = self.mps_status[vrs_path]
                # Get device type for this recording
                device_text = self._format_device_type(vrs_path, feature_status)
                table.add_row(
                    str(i),
                    str(vrs_path),
                    f"{get_pretty_size(await self._get_file_size(vrs_path))}",
                    device_text,
                    *[
                        self._apply_style(feature_status[feature])
                        for feature in self._mps.features
                    ],
                )
        self._table = table

    def watch_filter_mode(self) -> None:
        """Called when filter mode changes"""
        # Trigger table rebuild
        if self.mps_status:
            self.mps_status = dict(self.mps_status)

    def watch_sort_by(self) -> None:
        """Called when sort mode changes"""
        # Trigger table rebuild
        if self.mps_status:
            self.mps_status = dict(self.mps_status)

    def _format_progress_bar(self, progress: float) -> Text:
        """Create a text-based progress bar"""
        bar_width = 10
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        return Text.from_markup(f"[cyan]{bar}[/cyan] {progress:.0f}%")

    def _format_device_type(
        self, vrs_path: Path, feature_status: Dict[MpsFeature, ModelState]
    ) -> Any:
        """
        Format the device type display for a recording.

        - Show "AriaGen1" for AriaGen1
        - Show "AriaGen2" for AriaGen2
        - Show spinner during device type check
        - Show "Unknown" otherwise
        """

        # Get device type from the recording
        device_type = self._mps.get_device_type(vrs_path)
        if device_type == MpsAriaDevice.ARIA_GEN1:
            return Text.from_markup("[cyan]AriaGen1")
        elif device_type == MpsAriaDevice.ARIA_GEN2:
            return Text.from_markup("[yellow]AriaGen2")
        elif device_type == MpsAriaDevice.UNKNOWN:
            return Text.from_markup("Unknown")
        else:
            return Spinner("dots", "")

    def _apply_style(self, state: ModelState) -> Any:
        """
        Apply styling to the given state with enhanced error display and progress bars
        """
        if state.status == DisplayStatus.ERROR:
            error_code_url = "https://fb.me/mps-error-codes-gen2"
            return Text.from_markup(
                f":cross_mark: [red]{state.status}([blue underline][link={error_code_url}]{state.error_code}[/link][/blue underline])"
            )
        elif state.status == DisplayStatus.SUCCESS:
            return Text.from_markup(f":white_check_mark: [green]{state.status}")
        elif state.status == DisplayStatus.SCHEDULED:
            return Text.from_markup(f":clock1: [yellow]{state.status}")
        elif state.status in [
            DisplayStatus.UPLOADING,
            DisplayStatus.DOWNLOADING,
            DisplayStatus.ENCRYPTING,
            DisplayStatus.HASHING,
        ]:
            # Use progress bar for operations with progress
            icon_map = {
                DisplayStatus.UPLOADING: ":up_arrow:",
                DisplayStatus.DOWNLOADING: ":down_arrow:",
                DisplayStatus.ENCRYPTING: ":lock:",
                DisplayStatus.HASHING: ":key:",
            }
            icon = icon_map.get(state.status, ":gear:")
            progress_bar = self._format_progress_bar(state.progress or 0)
            text = Text()
            text.append_text(Text.from_markup(f"{icon} {state.status} "))
            text.append_text(progress_bar)
            return text
        return Spinner("dots", state.status)


class MpsApp(App):
    """MPS App that shows the current status of all recordings"""

    BINDINGS = [
        ("ctrl+q", "request_quit", "Quit"),
        ("d", "toggle_dark", "Dark Mode"),
        ("a", "filter_all", "Show All"),
        ("f", "filter_failed", "Failed Only"),
        ("s", "filter_success", "Success Only"),
        ("i", "filter_in_progress", "In Progress"),
        ("n", "sort_name", "Sort by Name"),
        ("t", "sort_status", "Sort by Status"),
        ("z", "toggle_sort_size", "Sort by Size"),
        ("h", "show_help", "Help"),
    ]
    CSS = """
    #top {
        height: 2;
    }
    #elapsed_time {
        width: auto;
        height: auto;
        dock: left;
        content-align: center middle;
        padding: 1 5;
    }
    #user {
        width: auto;
        height: auto;
        dock: right;
        content-align: center middle;
        padding: 1 5;
    }
    #stages_title {
        content-align: center middle;
        height:auto;
        padding: 1 0 0 0;
    }
    #stages {
        content-align: center middle;
        height:auto;
        padding: 1 0;
    }
    #status{
        content-align: center middle;
    }
    #status_title{
        content-align: center middle;
        padding: 2 0 1 0;
    }
    #log {
        height: auto;
        padding: 1 5;
    }
    """

    def __init__(self, args: argparse.Namespace, log_path: Path) -> None:
        self._args: argparse.Namespace = args
        self._log_path: Path = log_path
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        logger.info("Composing")
        yield Header()
        yield Horizontal(
            ElapsedTime(name="elapsed time", id="elapsed_time"),
            Static(
                "",
                name="user",
                id="user",
            ),
            id="top",
        )
        yield Static("EXPECTED STAGES", id="stages_title")
        yield Static(
            "[magenta]Hashing ->  HealthCheck  ->  Encryption  ->  Upload  ->  Scheduled  -> Processing  ->  Download Results  ->  Success",
            id="stages",
        )
        yield Rule()
        yield SummaryStats(self._mps)
        yield Static("[b]MPS REQUESTS", id="status_title")
        yield ScrollableContainer(StatusTable(self._mps), id="status")
        yield Rule()
        log_file_url = f"file://{self._log_path.absolute()}"
        log_text = Text.from_markup(":scroll: Log: [bold]")
        log_text.append(
            str(self._log_path), style="bold blue underline link " + log_file_url
        )
        yield Static(
            log_text,
            name="log file",
            id="log",
        )

        yield Footer()

    async def on_load(self) -> None:
        """Run when the app is loaded."""
        logger.info("on_load")
        self.title = "ARIA MACHINE PERCEPTION SERVICES"
        self._http_helper: HttpHelper = HttpHelper()
        self._authenticator: Authenticator = Authenticator(self._http_helper)
        args = self._args
        if args.username and args.password:
            await self._authenticator.password_login(
                args.username, args.password, args.save_token
            )
        elif await self._authenticator.load_and_validate_token():
            logger.debug("Using cached token.")
        self._mps: Mps = Mps(self._http_helper)

    async def on_mount(self) -> None:
        """Run when the app is mounted."""
        logger.info("on_mount")
        header = self.query_one(Header)
        header.title = "Aria Machine Perception Service"
        header.tall = True
        # Run MPS after login
        if self._authenticator.is_logged_in():
            # Check if keyring save failed and show notification
            if not self._authenticator.token_saved_to_keyring:
                self.notify(
                    "⚠️  Token saved in memory only. Keyring not available - you'll need to login again next time.",
                    severity="warning",
                    timeout=10,
                )
            self.run_mps()
        else:

            def __login_callback(success: bool) -> None:
                if self._authenticator.is_logged_in():
                    # Check if keyring save failed and show notification
                    if not self._authenticator.token_saved_to_keyring:
                        self.notify(
                            "⚠️  Token saved in memory only. Keyring not available - you'll need to login again next time.",
                            severity="warning",
                            timeout=10,
                        )
                    self.run_mps()
                else:
                    logger.debug("Failed to log in!")
                    self.exit()

            self.push_screen(UsernameScreen(), __login_callback)

    def _update_username(self) -> None:
        """Update the user name."""
        logger.debug(f"Setting username to {self._authenticator.user}")
        self.query_one("#user", Static).update(
            Text.from_markup(f"Username: [bold][cyan]{self._authenticator.user}"),
        )

    @work
    async def run_mps(self) -> None:
        """
        MPS worker task
        """
        self._http_helper.set_auth_token(self._authenticator.auth_token)
        self._update_username()
        self.query_one("#status_title", Static).update(
            f"[b] MPS REQUESTS - {self._args.mode.upper()}",
        )
        self.query_one("#elapsed_time", ElapsedTime).reset()
        await self._mps.run(self._args)

    async def action_request_quit(self) -> bool:
        """An action to quit the application."""

        async def __check_quit(quit_mode: QuitMode) -> None:
            """Called when QuitScreen is dismissed."""
            if quit_mode == QuitMode.LOGOUT_AND_QUIT:
                logger.debug("Logging out...")
                await self._authenticator.logout()
            if quit_mode in (QuitMode.QUIT, QuitMode.LOGOUT_AND_QUIT):
                logger.debug("Quitting...")
                await self._http_helper.close()
                return self.exit()
            if quit_mode == QuitMode.CANCEL:
                logger.debug("Dismissing QuitScreen...")

        self.push_screen(QuitScreen(), __check_quit)

    def action_filter_all(self) -> None:
        """Show all recordings"""
        status_table = self.query_one(StatusTable)
        status_table.set_filter("all")
        self.notify(
            "✓ Filter: All recordings (no filter applied)", severity="information"
        )

    def action_filter_failed(self) -> None:
        """Show only failed recordings"""
        status_table = self.query_one(StatusTable)
        status_table.set_filter("failed")
        self.notify(
            "✗ Filter: Failed only (at least one feature failed)",
            severity="warning",
        )

    def action_filter_success(self) -> None:
        """Show only successful recordings"""
        status_table = self.query_one(StatusTable)
        status_table.set_filter("success")
        self.notify(
            "✓ Filter: Success only (all features completed successfully)",
            severity="information",
        )

    def action_filter_in_progress(self) -> None:
        """Show only in-progress recordings"""
        status_table = self.query_one(StatusTable)
        status_table.set_filter("in_progress")
        self.notify(
            "⟳ Filter: In-progress only (at least one feature still processing)",
            severity="information",
        )

    def action_sort_name(self) -> None:
        """Toggle between ascending and descending name sort"""
        status_table = self.query_one(StatusTable)

        # Toggle between ascending and descending
        if status_table.sort_by == "name_asc":
            status_table.set_sort("name_desc")
            self.notify("Sorted by name ↓ (Z-A)", severity="information")
        else:
            # Default to ascending or switch from descending to ascending
            status_table.set_sort("name_asc")
            self.notify("Sorted by name ↑ (A-Z)", severity="information")

    def action_sort_status(self) -> None:
        """Sort recordings by status"""
        status_table = self.query_one(StatusTable)
        status_table.set_sort("status")
        self.notify(
            "Sorted by status (failed → in-progress → success)",
            severity="information",
        )

    def action_toggle_sort_size(self) -> None:
        """Toggle between ascending and descending size sort"""
        status_table = self.query_one(StatusTable)

        # Toggle between ascending and descending
        if status_table.sort_by == "size_asc":
            status_table.set_sort("size_desc")
            self.notify("Sorted by size ↓ (largest first)", severity="information")
        else:
            # Default to ascending or switch from descending to ascending
            status_table.set_sort("size_asc")
            self.notify("Sorted by size ↑ (smallest first)", severity="information")

    def action_show_help(self) -> None:
        """Show help/keyboard shortcuts"""
        help_text = """
[bold cyan]Keyboard Shortcuts:[/bold cyan]

[bold]Ctrl+Q[/bold] - Quit application
[bold]D[/bold] - Toggle dark mode

[bold cyan]Filters (mutually exclusive):[/bold cyan]
[bold]A[/bold] - Show all recordings (no filter)
[bold]F[/bold] - Failed: Shows recordings where at least one feature failed
[bold]S[/bold] - Success: Shows recordings where ALL features completed successfully
[bold]I[/bold] - In Progress: Shows recordings with at least one feature still processing

[bold cyan]Sorting:[/bold cyan]
[bold]N[/bold] - Sort by name (press repeatedly to toggle A-Z ↑↓)
[bold]T[/bold] - Sort by status (errors first, then in-progress, then success)
[bold]Z[/bold] - Sort by size (press repeatedly to toggle ↑↓)

[bold cyan]Help:[/bold cyan]
[bold]H[/bold] - Show this help

[bold cyan]Tips:[/bold cyan]
- Success filter requires ALL features to be successful (strict)
- Failed/In-progress filters show if ANY feature matches (lenient)
- Click blue error code links for detailed troubleshooting
        """
        self.notify(help_text, severity="information", timeout=15)
