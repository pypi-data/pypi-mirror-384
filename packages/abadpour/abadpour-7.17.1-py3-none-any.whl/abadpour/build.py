from bluer_objects import file

from abadpour import VERSION


def build() -> bool:
    return file.save_text(
        "_revision.tex",
        ["\\vspace{0.5cm}revision\\space" + VERSION + "\\space-\\space\\today"],
    )
