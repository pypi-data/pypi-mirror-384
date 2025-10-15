from __future__ import annotations

from contextlib import suppress


class XClsMakeYahwX:
    def __init__(self, ctx: object | None = None) -> None:
        # store optional orchestrator context for backward-compatible upgrades
        self._ctx = ctx

    def run(self) -> str:
        return "Hello world!"


def main() -> str:
    return XClsMakeYahwX().run()


if __name__ == "__main__":
    import logging
    import sys as _sys

    _LOGGER = logging.getLogger("x_make")

    def _info(*args: object) -> None:
        msg = " ".join(str(a) for a in args)
        with suppress(Exception):
            _LOGGER.info("%s", msg)
        if not _emit_print(msg):
            with suppress(Exception):
                _sys.stdout.write(msg + "\n")

    def _emit_print(msg: str) -> bool:
        with suppress(Exception):
            print(msg)
            return True
        return False

    _info(main())


x_cls_make_yahw_x = XClsMakeYahwX
