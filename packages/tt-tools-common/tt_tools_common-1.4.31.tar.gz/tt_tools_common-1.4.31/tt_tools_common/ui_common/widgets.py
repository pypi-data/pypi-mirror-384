# SPDX-FileCopyrightText: © 2024 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

from textual.app import RenderResult, ComposeResult
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Switch, Checkbox
from textual.widgets.data_table import CellDoesNotExist
from textual.containers import ScrollableContainer, Container, Grid, Horizontal
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import Markdown
from textual import on
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from rich.text import Text

from datetime import datetime
from typing import OrderedDict, Dict, List, Tuple, Callable, Union


class TTHeader(Widget):
    """A custom header widget for TT-Tools."""

    def __init__(self, app_name: str, app_version: str) -> None:
        super().__init__()
        self.app_name = app_name
        self.app_version = app_version

    def on_mount(self) -> None:
        self.set_interval(1, callback=self.refresh)

    def render(self) -> RenderResult:
        grid = Table.grid(expand=True, padding=(0, 1), pad_edge=True)
        grid.add_column(justify="left", ratio=0.25)
        grid.add_column(justify="center", ratio=0.5)
        grid.add_column(justify="right", ratio=0.25)

        version = f"Version {self.app_version}"
        app_name = self.app_name
        date = datetime.now().strftime("%b %d %Y %I:%M:%S %p")

        grid.add_row(version, app_name, date)

        return Panel(grid)


class TTFooter(Widget):
    """A custom footer widget for TT-Tools."""

    def __init__(self, content: List[str], justify: str = "center") -> None:
        super().__init__()
        self.content = content
        self.justify = justify

    def render(self) -> RenderResult:
        grid = Table.grid(expand=True, collapse_padding=False)
        for _ in range(len(self.content)):
            grid.add_column(justify=self.justify, ratio=1)
        grid.add_row(*self.content)

        return Panel(grid)


class TTDataTable(ScrollableContainer):
    """A custom container with a DataTable for TT-Tools."""

    def __init__(
        self, title: str, header: List[str] = None, id: str = None, **kwargs
    ) -> None:
        super().__init__(id=id)
        self.border_title = title
        self._title = title
        self.header = header
        self.dt = self.config_dt(**kwargs)

    def style_header(self):
        for i, header_text in enumerate(self.header):
            self.header[i] = Text(header_text, justify="center", style="underline")

    def config_dt(self, **kwargs) -> DataTable:
        # initialize DataTable
        dt = DataTable(id=self.id + "_table", **kwargs)

        # DT props
        dt.zebra_stripes = False
        dt.cursor_type = "cell"
        dt.border_title = self._title

        # TODO: if it doesn't make sense to initialize TTDataTable with header, can move it out to app
        # initialize Header
        if self.header:
            self.style_header()
            dt.add_columns(*self.header)

        return dt

    def update_data(self, rows: List[str]) -> None:
        # assert len(self.header) == max(
        #     [len(x)
        #      for x in rows]), "Data doesn't have expected num of columns"

        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                try:
                    # update cell values one by one
                    self.dt.update_cell_at(
                        coordinate=Coordinate(column=j, row=i), value=val
                    )
                except CellDoesNotExist:
                    # there are more rows than there used to be
                    self.dt.clear()
                    self.dt.add_rows(rows)

    def compose(self) -> ComposeResult:
        container = ScrollableContainer(self.dt, id=self.id)
        yield container


class TTMenu(Container):
    """A custom Menu/List widget for TT-Tools."""

    def __init__(self, id: str, title: str, data: OrderedDict[str, str]) -> None:
        super().__init__(id=id)
        self.border_title = title
        self.data = data
        self.justify_width = max([len(k) for k in data.keys()]) + 1

    def render(self) -> RenderResult:
        text = Text()
        for key, value in self.data.items():
            k = Text(
                f"{key.ljust(self.justify_width)}",
                style=Style(color="#ffd10a", bold=True),
            )
            if key == "Failed to fetch":
                text.append_text(k).append_text(
                    Text(f"\n{value}\n", style=Style(color="dark_orange"))
                )
            else:
                text.append_text(Text("* ")).append_text(k).append_text(
                    Text(f": {value}\n")
                )
        text.rstrip()

        return text


class TTHostCompatibilityMenu(Container):
    """
    A custom Menu/List widget for TT-Tools.
    Used in tt-smi to render Host Info with
    compatibility notes.

    Accepts dicts with string keys. If items
    are str, renders each item to a line akin
    to TTMenu. If item is Tuple of str, renders
    first item to the first line and second item
    to another line in red as a note.
    """

    def __init__(self, id: str, title: str, data: Dict[str, Union[str, Tuple]]) -> None:
        super().__init__(id=id)
        self.data = data
        self.justify_width = max([len(k) for k in self.data.keys()]) + 1

        # Are all values in the dict strings?
        fully_compatible = all([type(value) is str for value in self.data.values()])
        if fully_compatible:
            self.border_title = title + " (Fully Compatible)"
        else:
            self.border_title = title + " (Config Warning!)"
            self.styles.border_title_color = "red"

            self.border_subtitle = "* Recommended Config"
            self.styles.border_subtitle_color = "red"

    def render(self) -> RenderResult:
        text = Text()
        # Track the number of lines to set the widget height
        num_lines = 0
        for key, value in self.data.items():
            line_leader = Text("* ")
            # Render only one line
            if type(value) is str:
                num_lines += 1
                k = Text(
                    f"{key.ljust(self.justify_width)}" + ": ",
                    style=Style(color="#ffd10a", bold=True),
                )
                v = Text(f"{value}\n")
                text.append_text(line_leader).append_text(k).append_text(v)
            # Render two lines, the current state and the recommendation
            elif type(value) is tuple:
                num_lines += 2
                k = Text(
                    f"{key.ljust(self.justify_width)}" + ": ",
                    style=Style(color="#ffd10a", bold=True),
                )
                v_1 = Text(f"{value[0]}\n")
                v_2 = Text(
                    f"{' ' * (self.justify_width)}  * {value[1]}\n",
                    style=Style(color="dark_orange"),
                )

                text.append_text(line_leader).append_text(k).append_text(
                    v_1
                ).append_text(v_2)
            else:
                # TODO: Raise warning here?
                pass
        text.rstrip()

        self.styles.height = (
            4 + num_lines
        )  # Dynamically style widget height to fit all recommendations (+4 for border/padding)

        return text


class TTCompatibilityMenu(Container):
    """A custom Menu/List widget for TT-Tools."""

    def __init__(self, id: str, title: str, data: OrderedDict()) -> None:
        super().__init__(id=id)
        self.border_title = title
        self.data = data
        self.justify_width = max([len(k) for k in data.keys()]) + 1

    def render(self) -> RenderResult:
        text = Text()
        for key, value in self.data.items():
            if value[0] == True:
                k = Text(
                    f"{key.ljust(self.justify_width)}" + ": ",
                    style=Style(color="#ffd10a", bold=True),
                )
                text.append_text(Text("* ")).append_text(k).append_text(
                    Text(f"{value[1]}\n")
                )
            else:
                k = Text(
                    f"{key.ljust(self.justify_width)}" + ": ",
                    style=Style(color="#ffd10a", bold=True),
                )
                text.append_text(Text("* ")).append_text(k).append_text(
                    Text(f"{value[1]}\n", style=Style(color="dark_orange"))
                )
        text.rstrip()

        return text


class TTConfirmBox(ModalScreen):
    """A custom Confirm Box widget for TT-Tools."""

    def __init__(
        self, text: str, on_yes: Callable = None, on_no: Callable = None
    ) -> None:
        super().__init__()
        self.text = text
        self.on_yes = on_yes
        self.on_no = on_no
        # TODO: give border title

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.text, id="question"),
            Button("Yes", id="yes"),
            Button("No", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes" and self.on_yes:
            self.on_yes()
        elif event.button.id == "no" and self.on_no:
            self.on_no()
        self.app.pop_screen()


class TTHelperMenuBox(ModalScreen):
    """A custom modal screen with help options"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "esc_screen", "Escape the open screen"),
        ("h", "help", "Quit the help box"),
    ]

    def __init__(self, text: str, theme: OrderedDict = {}) -> None:
        super().__init__()
        self.text = text
        self.theme = theme

    def compose(self) -> ComposeResult:
        yield Markdown(self.text, id="help_menu_box")

    async def action_quit(self) -> None:
        """Return to main app"""
        self.app.pop_screen()

    async def action_esc_screen(self) -> None:
        """An action to select test to run"""
        self.app.pop_screen()

    async def action_quit(self) -> None:
        """Return to main app"""
        self.app.pop_screen()

    async def action_help(self) -> None:
        """Return to main app"""
        self.app.pop_screen()


class TTSettingsMenu(ModalScreen):
    """A custom modal screen with help options"""

    BINDINGS = [
        ("q, Q, s, S", "quit", "Quit"),
        ("escape", "esc_screen", "Escape the open screen"),
    ]

    def __init__(self, text: str, theme: OrderedDict = {}) -> None:
        super().__init__()
        self.text = text
        self.theme = theme

    def compose(self) -> ComposeResult:
        heading = "TT-SMI Settings"
        instruction = "(tab/mouse/enter: navigate dialogue box & update switches)"
        yield Grid(
            Label(Text(heading, style=self.theme["light_green_bold"]), id="heading"),
            Label(Text(instruction, style=self.theme["attention"]), id="instruction"),
            Label("o Dark Mode:         ", id="dark_label"),
            Switch(value=self.app.dark, id="dark_switch"),
            Label("o Latest SW versions:", id="sw_label"),
            Switch(value=self.app.get_latest_sw_vers, id="sw_switch"),
            id="settings_menu_box",
        )

    @on(Switch.Changed)
    def select_changed(self, event: Switch.Changed) -> None:
        """Switch event handler"""
        if event.switch.id == "dark_switch":
            # Toggle dark mode for app
            if event.switch.value == True:
                self.app.dark = True
            else:
                self.app.dark = False
        if event.switch.id == "sw_switch":
            # Toggle getting latest sw versions
            if event.switch.value == True:
                self.app.get_latest_sw_vers = True
            else:
                self.app.get_latest_sw_vers = False

    async def action_setting(self) -> None:
        """Return to main app"""
        self.app.pop_screen()

    async def action_esc_screen(self) -> None:
        """An action to select test to run"""
        self.app.pop_screen()

    async def action_quit(self) -> None:
        """Return to main app"""
        self.app.pop_screen()

    async def action_help(self) -> None:
        """Return to main app"""
        self.app.pop_screen()
