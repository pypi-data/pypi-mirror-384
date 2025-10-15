import os

from bluer_objects import file, README
from bluer_options.help.functions import get_help

from abadpour import NAME, VERSION, ICON, REPO_NAME
from abadpour.help.functions import help_functions


def build() -> bool:
    return all(
        README.build(
            items=readme.get("items", []),
            path=os.path.join(file.path(__file__), readme["path"]),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
        )
        for readme in [
            {
                "path": "../",
            },
            {
                "path": "./docs/abadpour.md",
            },
        ]
    )
