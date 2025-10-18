#!/usr/bin/env python3
"""
MixedAssembly CLI
"""
import argparse
import sys
from . import __version__
from . import remove_frameshifts as rf
from . import build_priors as bp
from . import run_mixed_assembly as rma


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    # si el usuario no da subcomando o pide --help general
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print(f"""
MixedAssembly {__version__}

Usage:
  mixedassembly <subcommand> [options]

Available subcommands:
  remove-frameshifts   Remove frameshifts from an alignment
  build-priors         Build priors parquet file
  run-mixed-assembly   Run mixed assembly pipeline

Use 'mixedassembly <subcommand> -h' for details on each one.
""")
        sys.exit(0)

    if argv[0] in ("--version", "-v", "-V"):
        print(f"mixedassembly {__version__}")
        sys.exit(0)

    # delegar completamente al módulo correspondiente
    subcmd = argv[0]
    subargs = argv[1:]

    if subcmd == "remove-frameshifts":
        sys.exit(rf.main(subargs))
    elif subcmd == "build-priors":
        sys.exit(bp.main(subargs))
    elif subcmd == "run-mixed-assembly":
        sys.exit(rma.main(subargs))
    else:
        print(f"Unknown command: {subcmd}")
        print("Use 'mixedassembly --help' for available commands.")
        sys.exit(1)


if __name__ == "__main__":
    main()
