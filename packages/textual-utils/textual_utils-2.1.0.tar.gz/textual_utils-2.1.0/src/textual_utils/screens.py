from typing import Any, Union

from config.settings import SettingOptions, SettingType
from i18n import tr
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Center, Grid
from textual.screen import ModalScreen
from textual.types import NoSelection
from textual.widgets import Button, Label, Link, Select, Static, Switch

from textual_utils.app_metadata import AppMetadata

BORDER_WIDTH = 1
PADDING_WIDTH = 3
BOX_WIDTH = 2 * BORDER_WIDTH + 2 * PADDING_WIDTH

BUTTON_WIDTH = 16

GUTTER_WIDTH = 2

SELECT_BOX_WIDTH = 8

SWITCH_WIDTH = 10


class AboutScreen(ModalScreen[None]):
    CSS_PATH = ["screens.tcss", "about_screen.tcss"]

    def __init__(self, current_app: App[Any], app_metadata: AppMetadata) -> None:
        super().__init__()

        self.current_app = current_app

        self.app_metadata = app_metadata
        self.app_name = (
            f"{self.app_metadata.name} {self.app_metadata.version}"
            f"  {self.app_metadata.icon}"
        )

    def compose(self) -> ComposeResult:
        self.dialog = Grid(
            Label(Text(self.app_name, style="bold green")),
            Label(
                Text(
                    tr(self.app_metadata.description),
                    style="italic cornflowerblue",
                )
            ),
            Static(),
            Label(tr(self.app_metadata.author)),
            Link(self.app_metadata.email, url=f"mailto:{self.app_metadata.email}"),
            Center(Button("Ok", variant="primary", id="ok")),
            id="about_dialog",
        )

        yield self.dialog

    def on_mount(self) -> None:
        self.dialog.border_title = tr("About")
        self.dialog.border_subtitle = self.app_metadata.name

        max_label_length = max(
            len(self.app_name),
            len(tr(self.app_metadata.description)),
            len(tr(self.app_metadata.author)),
            len(self.app_metadata.email),
        )

        self.dialog.styles.width = BOX_WIDTH + max_label_length
        self.dialog.styles.min_width = BOX_WIDTH + BUTTON_WIDTH

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.current_app.pop_screen()


class ConfirmScreen(ModalScreen[bool]):
    CSS_PATH = ["screens.tcss", "confirm_screen.tcss"]

    def __init__(self, dialog_title: str, dialog_subtitle: str, question: str) -> None:
        super().__init__()

        self.dialog_title = tr(dialog_title)
        self.dialog_subtitle = tr(dialog_subtitle)
        self.question = tr(question)

    def compose(self) -> ComposeResult:
        self.dialog = Grid(
            Label(self.question, id="question"),
            Grid(
                Button(tr("Yes"), variant="primary", id="yes"),
                Button(tr("No"), variant="error", id="no"),
                id="buttons",
            ),
            id="confirm_dialog",
        )

        yield self.dialog

    def on_mount(self) -> None:
        self.dialog.border_title = self.dialog_title
        self.dialog.border_subtitle = self.dialog_subtitle

        def odd_len(s: str) -> bool:
            return len(s) % 2 != 0

        yes_str = tr("Yes")
        no_str = tr("No")

        if odd_len(yes_str):
            yes_btn = self.query_one("#yes", Button)
            yes_btn_width = yes_btn.styles.min_width = BUTTON_WIDTH - 1
        else:
            yes_btn_width = BUTTON_WIDTH

        if odd_len(no_str):
            no_btn = self.query_one("#no", Button)
            no_btn_width = no_btn.styles.min_width = BUTTON_WIDTH - 1
        else:
            no_btn_width = BUTTON_WIDTH

        buttons = self.query_one("#buttons", Grid)
        if odd_len(self.question):
            btn_gutter_width = buttons.styles.grid_gutter_vertical = GUTTER_WIDTH + 1
        else:
            btn_gutter_width = buttons.styles.grid_gutter_vertical = GUTTER_WIDTH

        self.dialog.styles.width = BOX_WIDTH + len(self.question)
        self.dialog.styles.min_width = (
            BOX_WIDTH + yes_btn_width + btn_gutter_width + no_btn_width
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class SettingsScreen(ModalScreen[bool]):
    CSS_PATH = ["screens.tcss", "settings_screen.tcss"]

    def __init__(
        self,
        dialog_title: str,
        dialog_subtitle: str,
        settings: list[SettingType],
    ) -> None:
        super().__init__()

        self.dialog_title = tr(dialog_title)
        self.dialog_subtitle = tr(dialog_subtitle)

        self.settings = settings

        self.widgets: list[Union[Select[str], Switch]] = []

    def compose(self) -> ComposeResult:
        self.dialog = Grid(id="settings_dialog")

        self.dialog.border_title = self.dialog_title
        self.dialog.border_subtitle = self.dialog_subtitle

        max_select_width = 0
        switch_exists = False

        with self.dialog:
            for setting in self.settings:
                setting.old_value = setting.current_value  # type: ignore[assignment]

                yield Label(tr(setting.label))

                widget: Select[str] | Switch

                if isinstance(setting, SettingOptions):
                    options = [
                        (tr(option.display_str), option.value)
                        for option in setting.options
                    ]
                    widget = Select(
                        options=options,
                        allow_blank=False,
                        value=setting.current_value,
                    )
                    select_width = max(len(t[0]) for t in options) + SELECT_BOX_WIDTH
                    widget.styles.width = select_width

                    if select_width > max_select_width:
                        max_select_width = select_width

                else:
                    widget = Switch(value=setting.current_value)
                    switch_exists = True

                yield widget
                self.widgets.append(widget)

            yield Grid(
                Button(tr("Save"), variant="primary", id="save"),
                Button(tr("Cancel"), variant="error", id="cancel"),
                id="buttons",
            )

        label_lengths = [len(tr(setting.label)) for setting in self.settings]
        max_label_length = 0 if not label_lengths else max(label_lengths)

        if switch_exists:
            max_widget_width = max(SWITCH_WIDTH, max_select_width)
        else:
            max_widget_width = max_select_width

        self.dialog.styles.width = (
            BOX_WIDTH + max_label_length + GUTTER_WIDTH + max_widget_width
        )

        self.dialog.styles.min_width = (
            BOX_WIDTH + BUTTON_WIDTH + GUTTER_WIDTH + BUTTON_WIDTH
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":

            def value_or_default(
                v: str | bool | NoSelection, default: str = ""
            ) -> str | bool:
                return v if not isinstance(v, NoSelection) else default

            for setting, widget in zip(self.settings, self.widgets):
                setting.current_value = value_or_default(widget.value)  # type: ignore[assignment]

            self.dismiss(True)
        else:
            self.dismiss(False)
