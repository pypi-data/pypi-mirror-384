# app.py
#
# Copyright (c) 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

from textual.app import App, ComposeResult
from textual.color import Color
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Digits, Footer, Header, Static

from wretched_tower.tower import EmptyTowerError, PerilLevel, Tower


def get_dice_display(dice_left: int) -> str:
    return str(dice_left) if dice_left > 0 else "☠️ 0 ☠️"


def get_tower_color_from_peril_level(peril_level: PerilLevel) -> Color:
    match peril_level:
        case PerilLevel.MORTALITY:
            return Color.parse("orange")
        case PerilLevel.WOUNDED:
            return Color.parse("yellow")
        case PerilLevel.DEAD:
            return Color.parse("red")
        case PerilLevel.HEALTHY:
            return Color.parse("green")
        case _:  # no cov
            return Color.parse("green")


def get_peril_meter_display_from_peril_level(peril_level: PerilLevel) -> str:
    match peril_level:
        case PerilLevel.MORTALITY:
            return "MORTAL DANGER"
        case PerilLevel.WOUNDED:
            return "WOUNDED"
        case PerilLevel.DEAD:
            return "DEAD"
        case PerilLevel.HEALTHY:
            return "HEALTHY"
        case _:  # no cov
            return "HEALTHY"


class DiceCounter(Digits):
    pass


class PerilMeter(Static):
    pass


class TowerStatus(Widget):
    """A widget that displays the current status of the tower."""

    peril_level = reactive(PerilLevel.HEALTHY)
    tower_color = reactive(Color.parse("green"))

    def __init__(self, tower: Tower, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        super().__init__()
        self.peril_level = tower.get_peril_level()
        self.tower_color = get_tower_color_from_peril_level(self.peril_level)

    def compose(self) -> ComposeResult:
        yield Static("[b]Dice Remaining[/b]")
        yield DiceCounter("100", id="dice")
        yield PerilMeter(get_peril_meter_display_from_peril_level(self.peril_level))
        yield DataTable(name="Roll Results")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Rolled", "1", "2", "3", "4", "5", "6")

    def watch_tower_color(self, color: Color) -> None:
        self.styles.color = color

    def watch_peril_level(self, peril_level: PerilLevel) -> None:
        self.tower_color = get_tower_color_from_peril_level(peril_level)


class TowerApp(App):
    """A TUI that manages a tumbling tower mechanic via die rolls."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "roll_tower", "Roll tower dice"),
        ("ctrl+n", "new_tower", "Start new tower"),
    ]
    TITLE = "Wretched Tower"
    # theme = "tokyo-night"
    tower = Tower()

    CSS = """
        TowerStatus Static {
            text-align: center;
        }
        DiceCounter {
            text-align: center;
        }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield TowerStatus(tower=self.tower, id="status")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggles between dark and light mode."""
        self.theme = (  # type: ignore
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_roll_tower(self) -> None:
        """Roll the tower and send the results to the child widgets as needed."""
        try:
            self.tower.roll_tower()
            dice_left = self.tower.get_dice_left()
            tower_status_widget = self.query_one(TowerStatus)
            tower_status_widget.peril_level = self.tower.get_peril_level()
            self.query_one(DiceCounter).update(get_dice_display(dice_left))
            self.query_one(PerilMeter).update(
                get_peril_meter_display_from_peril_level(
                    tower_status_widget.peril_level
                )
            )
            last_result = self.tower.roll_distributions[-1]
            tower_status_widget.query_one(DataTable).add_row(
                last_result.dice_rolled,
                last_result.dice_results[1],
                last_result.dice_results[2],
                last_result.dice_results[3],
                last_result.dice_results[4],
                last_result.dice_results[5],
                last_result.dice_results[6],
            )
            if dice_left == 0:
                self.notify("[b][red]You Have Died[/red][/b]")
        except EmptyTowerError:
            self.notify("You are already dead.", severity="error")

    def action_new_tower(self) -> None:
        self.tower = Tower()
        dice_left = self.tower.get_dice_left()
        tower_status_widget = self.query_one(TowerStatus)
        self.query_one(DiceCounter).update(get_dice_display(dice_left))
        tower_status_widget.peril_level = self.tower.get_peril_level()
        self.query_one(PerilMeter).update(
            get_peril_meter_display_from_peril_level(tower_status_widget.peril_level)
        )
        tower_status_widget.query_one(DataTable).clear()
