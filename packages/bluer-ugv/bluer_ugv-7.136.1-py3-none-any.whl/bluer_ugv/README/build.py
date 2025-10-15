import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_ugv import NAME, VERSION, ICON, REPO_NAME
from bluer_ugv.help.functions import help_functions
from bluer_ugv.README import (
    alias,
    beast,
    eagle,
    fire,
    ravin,
    root,
    shield,
    arzhang,
    rangin,
    swallow,
    UGVs,
)


def build() -> bool:
    return all(
        README.build(
            items=readme.get("items", []),
            path=os.path.join(file.path(__file__), readme["path"]),
            cols=readme.get("cols", 3),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
            macros=readme.get("macros", {}),
        )
        for readme in root.docs
        + beast.docs
        + eagle.docs
        + fire.docs
        + ravin.docs
        + shield.docs
        + arzhang.docs
        + swallow.docs
        + alias.docs
        + UGVs.docs
        + rangin.docs
    )
