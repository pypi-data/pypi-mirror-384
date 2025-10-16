import logging
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import parse
from pzp import pzp
from tomlkit import array, dump, load
from trove_classifiers import sorted_classifiers

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Add classifiers to pyproject.toml")
    parser.add_argument(
        "--pyproject",
        nargs="?",
        type=Path,
        default="pyproject.toml",
        help="Path to pyproject %(default)s",
    )

    subparsers = parser.add_subparsers(dest="command")
    # Used to add subcommands
    # currently not using anything except global params
    subcommands = [
        parser,
        subparsers.add_parser("add"),
        subparsers.add_parser("suggest"),
    ]
    for subcommand in subcommands:
        subcommand.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING - args.verbose * 10)

    match args.command:
        case "add":
            return add(args)
        case "suggest":
            return suggest(args)
        case None:
            parser.print_help()


def add(args):
    choice = pzp(sorted_classifiers)
    if choice is None:
        logger.info("User exited without choosing")
        return 1
    if args.pyproject.exists():
        with args.pyproject.open("rb") as fp:
            pyproject = load(fp)
            try:
                classifiers = set(pyproject["project"]["classifiers"])
            except KeyError:
                classifiers = set()

            classifiers.add(choice)

            tbl = array()
            tbl.multiline(True)
            tbl.extend(sorted(classifiers))
            pyproject["project"]["classifiers"] = tbl
        with args.pyproject.open("w") as fp:
            dump(pyproject, fp)


def suggest(args):
    # Sort and filter the classifiers that we can check for
    python_classifiers = {}
    package_classifiers = defaultdict(dict)

    for classifier in sorted_classifiers:
        match classifier.split(" :: "):
            case "Programming Language", "Python", version:
                try:
                    python_classifiers[parse(version.strip())] = classifier
                except Exception:
                    logger.info("Unable to parse Python version %s", version)
            case "Framework", "Django", version:
                try:
                    package_classifiers["django"][parse(version.strip())] = classifier
                except Exception:
                    logger.info("Unable to parse Django version %s", version)

    # Start checking our pyproject file for what classifiers we think we can add
    suggested_addition = set()
    suggested_removal = set()
    with args.pyproject.open("rb") as fp:
        pyproject = load(fp)
        if "requires-python" in pyproject["project"]:
            dep = SpecifierSet(pyproject["project"]["requires-python"])
            for version in python_classifiers:
                if dep.contains(version):
                    suggested_addition.add(python_classifiers[version])
                else:
                    suggested_removal.add(python_classifiers[version])

        # Any project specific dependencies that we want to support
        for dep in pyproject["project"].get("dependencies", []):
            dep = Requirement(dep)
            lookup = dep.name.lower()
            if lookup in package_classifiers:
                for version in package_classifiers[lookup]:
                    if dep.specifier.contains(version):
                        suggested_addition.add(package_classifiers[lookup][version])
                    else:
                        suggested_removal.add(package_classifiers[lookup][version])

    try:
        classifiers = set(pyproject["project"]["classifiers"])
    except KeyError:
        classifiers = set()

    classifiers.update(suggested_addition)
    classifiers.difference_update(suggested_removal)

    tbl = array()
    tbl.multiline(True)
    tbl.extend(sorted(classifiers))
    pyproject["project"]["classifiers"] = tbl
    with args.pyproject.open("w") as fp:
        dump(pyproject, fp)


if __name__ == "__main__":
    main()
