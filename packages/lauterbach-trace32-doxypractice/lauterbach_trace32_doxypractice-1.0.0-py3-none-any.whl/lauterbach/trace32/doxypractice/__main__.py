#
# SPDX-FileCopyrightText: 2025 Lauterbach GmbH
#
# SPDX-License-Identifier: MIT
#

import argparse
import logging

from lauterbach.trace32.doxypractice.doxypractice import DoxyPractice

logging.basicConfig(filename="pygls.log", level=logging.DEBUG, filemode="w")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doxypractice",
        description="Language filter for Doxygen that adds support for Lauterbach TRACE32 scripts. It translates TRACE32 scripts into a C-like format that is understood by Doxygen.",
    )
    _ = parser.add_argument("script", help="PRACTICE script to parse")

    args = parser.parse_args()

    doxypractice = DoxyPractice()
    doxypractice.parse(cmm=args.script)


if __name__ == "__main__":
    main()
