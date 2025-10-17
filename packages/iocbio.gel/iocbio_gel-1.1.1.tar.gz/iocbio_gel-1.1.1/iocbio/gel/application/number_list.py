#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np


def numbers_to_string(lanes):
    """
    Creates a human-readable string from list.
    Returns a range if lanes are sequential, otherwise a comma separated list or a '-' if no lanes
    """
    n = len(lanes) - 1
    if n < 0:
        return "-"
    if n < 1:
        return str(min(lanes))
    if sum(np.diff(sorted(lanes)) == 1) >= n:
        return f"{min(lanes)}-{max(lanes)}"
    return ",".join(map(str, lanes))


def string_to_numbers(lanes: str) -> list:
    """
    Splits human-readable string list to array.
    """
    if not lanes or lanes == "-":
        return []
    if "," in lanes:
        return list(map(int, lanes.split(",")))
    if "-" in lanes:
        min_lane, max_lane = list(map(int, lanes.split("-")))
        return list(range(min_lane, max_lane + 1))
    if lanes.isdigit():
        return [int(lanes)]
    return []
