from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_sbc import ALIAS


def help_cd(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@sbc",
            "parts",
            "cd",
        ],
        "cd to part images.",
        mono=mono,
    )


def help_adjust(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun,~grid", mono=mono)

    args = [
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@sbc",
            "parts",
            "adjust",
            f"[{options}]",
        ]
        + args,
        "adjust part images.",
        mono=mono,
    )


help_functions = {
    "adjust": help_adjust,
    "cd": help_cd,
}
