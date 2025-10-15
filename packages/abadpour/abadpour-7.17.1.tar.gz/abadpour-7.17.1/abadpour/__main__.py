from blueness.argparse.generic import main

from abadpour import NAME, VERSION, DESCRIPTION, ICON
from abadpour import build, README
from abadpour.logger import logger

main(
    ICON=ICON,
    NAME=NAME,
    DESCRIPTION=DESCRIPTION,
    VERSION=VERSION,
    main_filename=__file__,
    tasks={
        "build": lambda _: build.build(),
        "build_README": lambda _: README.build(),
    },
    logger=logger,
)
