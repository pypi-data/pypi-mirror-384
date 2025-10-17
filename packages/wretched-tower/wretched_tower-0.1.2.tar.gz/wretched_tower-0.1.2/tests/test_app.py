# test_app.py
#
# Copyright (c) 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from textual.color import Color

from wretched_tower.app import (
    DiceCounter,
    PerilMeter,
    TowerApp,
    TowerStatus,
    get_dice_display,
    get_peril_meter_display_from_peril_level,
    get_tower_color_from_peril_level,
)
from wretched_tower.tower import PerilLevel


@pytest.mark.parametrize(
    "dice_value,expected_output",
    [(100, "100"), (75, "75"), (23, "23"), (0, "☠️ 0 ☠️"), (-2, "☠️ 0 ☠️")],
)
def test_get_dice_display(dice_value, expected_output):
    assert get_dice_display(dice_value) == expected_output


@pytest.mark.parametrize(
    "peril_level,expected_color",
    [
        (PerilLevel.HEALTHY, Color.parse("green")),
        (PerilLevel.WOUNDED, Color.parse("yellow")),
        (PerilLevel.MORTALITY, Color.parse("orange")),
        (PerilLevel.DEAD, Color.parse("red")),
    ],
)
def test_get_tower_color_from_peril_level(peril_level, expected_color):
    assert get_tower_color_from_peril_level(peril_level) == expected_color


@pytest.mark.parametrize(
    "peril_level,expected_output",
    [
        (PerilLevel.HEALTHY, "HEALTHY"),
        (PerilLevel.WOUNDED, "WOUNDED"),
        (PerilLevel.MORTALITY, "MORTAL DANGER"),
        (PerilLevel.DEAD, "DEAD"),
    ],
)
def test_get_peril_meter_display_from_peril_level(peril_level, expected_output):
    assert get_peril_meter_display_from_peril_level(peril_level) == expected_output


def test_app_layout(snap_compare) -> None:
    assert snap_compare("../src/wretched_tower/app.py")


@pytest.mark.asyncio
async def test_dark_mode_toggle() -> None:
    app = TowerApp()
    async with app.run_test() as pilot:
        await pilot.press("d")
        assert app.theme == "textual-light"
        await pilot.press("d")
        assert app.theme == "textual-dark"


@pytest.mark.asyncio
async def test_roll_display() -> None:
    app = TowerApp()
    async with app.run_test() as pilot:
        assert pilot.app.query_one(TowerStatus).styles.color == Color.parse("green")
        while pilot.app.tower.get_dice_left() > 0:
            await pilot.press("r")
            await pilot.pause()
            dice_left = pilot.app.tower.get_dice_left()
            if dice_left == 0:
                assert len(pilot.app._notifications) == 1
            assert pilot.app.query_one(DiceCounter).value == get_dice_display(
                dice_left
            )
            displayed_color = pilot.app.query_one(TowerStatus).styles.color
            tower_status = app.query_one(TowerStatus)
            assert tower_status.peril_level == pilot.app.tower.get_peril_level()
            assert pilot.app.query_one(
                PerilMeter
            )._content == get_peril_meter_display_from_peril_level(
                pilot.app.tower.get_peril_level()
            )
            match pilot.app.tower.get_peril_level():
                case PerilLevel.HEALTHY:
                    assert displayed_color == Color.parse("green")
                case PerilLevel.WOUNDED:
                    assert displayed_color == Color.parse("yellow")
                case PerilLevel.MORTALITY:
                    assert displayed_color == Color.parse("orange")
                case PerilLevel.DEAD:
                    assert displayed_color == Color.parse("red")


@pytest.mark.asyncio
async def test_new_tower() -> None:
    app = TowerApp()
    async with app.run_test() as pilot:
        pilot.app.tower._dice_left = 80
        await pilot.press("r")
        await pilot.pause()
        assert pilot.app.query_one(DiceCounter).value != "100"
        await pilot.press("ctrl+n")
        await pilot.pause()
        assert pilot.app.query_one(DiceCounter).value == "100"


@pytest.mark.asyncio
async def test_already_dead_notification() -> None:
    app = TowerApp()
    async with app.run_test() as pilot:
        app.tower._dice_left = 0
        assert len(pilot.app._notifications) == 0
        await pilot.press("r")
        await pilot.pause()
        assert len(pilot.app._notifications) == 1
