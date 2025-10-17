# test_tower.py
#
# Copyright (c) 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from wretched_tower.tower import EmptyTowerError, PerilLevel, Tower


@pytest.mark.parametrize(
    "dice_size,expected_results",
    [
        (6, [1, 2, 3, 4, 5, 6]),
        (10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        (8, [1, 2, 3, 4, 5, 6, 7, 8]),
    ],
)
def test_possible_die_values(dice_size, expected_results) -> None:
    tower = Tower(dice_size=dice_size)
    assert tower.possible_values == expected_results


@pytest.mark.parametrize("dice_size", [-1, 0, 1])
def test_invalid_dice_size(dice_size) -> None:
    with pytest.raises(ValueError):
        Tower(dice_size=dice_size)


@pytest.mark.parametrize("dice_amount", [-2, 104])
def test_invalid_dice_amount(dice_amount) -> None:
    with pytest.raises(ValueError):
        Tower(dice_amount=dice_amount)


@pytest.mark.parametrize(
    "dice_size,expected_dict",
    [
        (6, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}),
        (10, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0}),
    ],
)
def test_generate_result_dict(dice_size, expected_dict) -> None:
    tower = Tower(dice_size=dice_size)
    assert tower.get_result_dict_template() == expected_dict


def test_tower_roll() -> None:
    expected_dice = 100
    tower = Tower()
    assert expected_dice == tower.get_dice_left()
    assert len(tower.roll_distributions) == 0
    tower.roll_tower()
    assert len(tower.roll_distributions) == 1
    assert expected_dice == tower.roll_distributions[0].dice_rolled
    assert (
        tower.get_dice_left()
        == expected_dice - tower.roll_distributions[0].dice_results[1]
    )
    expected_dice = tower.get_dice_left()
    tower.roll_tower()
    assert len(tower.roll_distributions) == 2
    assert expected_dice == tower.roll_distributions[1].dice_rolled
    assert (
        tower.get_dice_left()
        == expected_dice - tower.roll_distributions[1].dice_results[1]
    )
    for distribution in tower.roll_distributions:
        total_dice_rolled = 0
        for _key, value in distribution.dice_results.items():
            total_dice_rolled += value
        assert total_dice_rolled == distribution.dice_rolled


@pytest.mark.parametrize(
    "dice_amount,expected_peril",
    [
        (100, PerilLevel.HEALTHY),
        (75, PerilLevel.HEALTHY),
        (59, PerilLevel.WOUNDED),
        (28, PerilLevel.WOUNDED),
        (24, PerilLevel.MORTALITY),
    ],
)
def test_tower_peril_calculation(dice_amount, expected_peril) -> None:
    tower = Tower(dice_amount=dice_amount)
    assert tower.get_peril_level() == expected_peril


def test_tower_peril_dead() -> None:
    tower = Tower()
    # Use private access to this property to mimic the dead scenario.
    tower._dice_left = 0
    assert tower.get_peril_level() == PerilLevel.DEAD
    with pytest.raises(EmptyTowerError):
        tower.roll_tower()
