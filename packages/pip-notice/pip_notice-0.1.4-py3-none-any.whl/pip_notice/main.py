from importlib.metadata import distributions
from tempfile import mkstemp
from .vendor.typeguard import check_type
from argparse import ArgumentParser
from sys import stderr
import json
import os
import re

NOTICE_HEADER = """\
This product includes software developed by the following third-party projects:

"""

PATTERN_DELIMITER = re.compile(r"[-_.]+")


def license_name_to_text(license_name: str) -> str | None:
    if license_name == "N/A":
        return ""
    return None


def normalize_pkg_name(pkg_name: str) -> str:
    return PATTERN_DELIMITER.sub("-", pkg_name).lower()


def search_file(path: str, filename: str) -> str | None:
    for root, _, files in os.walk(path):
        if filename in files:
            return f"{root}/{filename}"
    return None


def collect(output_path: str, ignore: list[str]):
    skip: dict[str, list | None] = {}
    for pkg in ignore:
        if "==" in pkg:
            name, version = pkg.rsplit("==", 1)
            if (skip_versions := skip.get(name, [])) is not None:
                skip[name] = skip_versions + [version]
        else:
            skip[pkg] = None

    licenses = {}
    for dist in distributions():
        name = normalize_pkg_name(check_type(dist.metadata["Name"], str))
        skip_versions = skip.get(name, [])
        if skip_versions is None:
            continue

        version = check_type(dist.metadata["version"], str)
        if version in skip_versions:
            continue

        author = None
        if author_ := dist.metadata.get("Author"):
            author = author_
        if (author_email := dist.metadata.get("Author-Email")) and "<" in author_email:
            author = author_
        elif maintainer := dist.metadata.get("Maintainer"):
            author = maintainer + " (Maintainer)"
        elif (
            maintainer_email := dist.metadata.get("Maintainer-Email")
        ) and "<" in maintainer_email:
            author = maintainer_email.split("<")[0].strip() + " (Maintainer)"

        license_texts = set()
        license_expressions = dist.metadata.get_all("License-Expression", [])
        license_names_ = check_type(license_expressions, list[str])
        license_names = set(license_names_)

        licenses_ = dist.metadata.get_all("License", [])
        license_infos = check_type(licenses_, list[str])
        for text in license_infos:
            if "\n" in text:
                license_texts.add(text)
            else:
                license_names.add(text)

        classifiers = dist.metadata.get_all("Classifier", [])
        for classifier in check_type(classifiers, list[str]):
            if classifier.startswith("License :: "):
                license_names.add(classifier.split(" :: ")[-1].strip())

        license_files = dist.metadata.get_all("License-File", [])
        license_files = check_type(license_files, list[str])
        if len(license_names) != 0 or len(license_files) != 0:
            if len(license_files) == 0:
                license_files = [
                    "LICENSE",
                    "LICENSE.md",
                    "LICENSE.txt",
                    "License",
                    "License.md",
                    "License.txt",
                ]
            for license_file in license_files:
                license_path = search_file(dist._path, license_file)  # type: ignore
                if license_path is not None:
                    with open(f"{license_path}", "rb") as file:
                        license_texts.add(file.read().decode(errors="replace"))

        licenses[f"{name}=={version}"] = {
            "author": author,
            "licenses": list(license_names),
            "license_texts": list(license_texts),
        }

    with open(output_path, "w") as file:
        json.dump(licenses, file)


def input_select(inputs, prompt):
    print(">>", prompt, file=stderr)
    for i, text in enumerate(inputs):
        text = text.strip()
        if "\n" in text:
            line = text.split("\n", 1)[0] + " ..."
        else:
            line = text
        print(f"{i + 1}: {line}", file=stderr)
    print("Choice: ", end="", file=stderr)
    return int(input().strip())-1


def select(input_paths, output_path):
    all_licenses = {}
    for input_path in input_paths:
        with open(input_path) as file:
            licenses = json.load(file)
        for key, info in licenses.items():
            if key in all_licenses:
                assert info == all_licenses[key]
            all_licenses[key] = info

    for key, info in all_licenses.items():
        name, version = key.split("==", 1)
        print(f"Processing {name}=={version}..", file=stderr)

        license_names = list(set(info["licenses"]))
        license_texts = list(set(info["license_texts"]))

        if len(license_names) == 0:
            print("License name: ", end="", file=stderr, flush=True)
            info["licenses"] = [input().strip()]
        elif len(license_names) > 1:
            choice = input_select(license_names + ["N/A"], "Choose license")
            info["licenses"] = [(license_names + ["N/A"])[choice]]

        if len(license_texts) == 0:
            info["license_texts"] = [
                license_name_to_text(info["licenses"][0]) or "<missing>"
            ]
        elif len(license_texts) > 1:
            choice = input_select(license_texts + ["N/A"], "Choose license text")
            info["license_texts"] = [(license_texts + [""])[choice]]

    with open(output_path, "w") as file:
        json.dump(all_licenses, file)


def generate(input_path, output_path):
    with open(input_path) as file:
        licenses = json.load(file)

    with open(output_path, "w") as file:
        file.write(NOTICE_HEADER)
        for key, info in licenses.items():
            name, version = key.split("==", 1)
            license_name = info["licenses"][0]
            file.write(f"# {name} (Version {version})\n")
            author = info.get("author")
            if author is not None:
                file.write(f"Copyright (c): {author}\n")
            file.write(f"Licensed under: {license_name}\n")
            file.write("\n")
        file.write("\n" * 2)
        for key, info in licenses.items():
            name, version = key.split("==", 1)
            title = f" {name} {version} "
            n = 80 - len(title)
            file.write("=" * (n // 2) + title + "=" * (n - n // 2) + "\n" * 3)
            file.write(info["license_texts"][0].strip("\n") + "\n" * 3)


def main():
    parser = ArgumentParser(
        description="Python project NOTICE file generator", allow_abbrev=True
    )

    commands_group = parser.add_subparsers(dest="command", title="Commands")

    collect_parser = commands_group.add_parser(
        "collect", help="collect dependencies into json format"
    )
    select_parser = commands_group.add_parser(
        "select", help="select / fix license info and combine license collections"
    )
    generate_parser = commands_group.add_parser(
        "generate", help="generate NOTICE file from licenses.json"
    )
    direct_parser = commands_group.add_parser("direct", help="generate NOTICE directly")

    collect_parser.add_argument(
        "-i", "--ignore", metavar="pkg", action="append", default=[]
    )
    collect_parser.add_argument(
        "-o", "--output", metavar="licenses.json", default="/dev/stdout"
    )

    select_parser.add_argument("input", nargs="+", metavar="licenses.json")
    select_parser.add_argument(
        "-o", "--output", metavar="select.json", default="/dev/stdout"
    )

    generate_parser.add_argument("input", metavar="licenses.json")
    generate_parser.add_argument(
        "-o", "--output", metavar="NOTICE", default="/dev/stdout"
    )

    direct_parser.add_argument(
        "-i", "--ignore", metavar="pkg[==version]", action="append", default=[]
    )
    direct_parser.add_argument(
        "-o", "--output", metavar="licenses.json", default="/dev/stdout"
    )

    args = parser.parse_args()

    if args.command == "collect":
        args.ignore.append("pip-notice")
        collect(args.output, args.ignore)
    elif args.command == "select":
        select(args.input, args.output)
    elif args.command == "generate":
        generate(args.input, args.output)
    elif args.command == "direct":
        args.ignore.append("pip-notice")
        _, tmp1 = mkstemp()
        collect(tmp1, args.ignore)
        _, tmp2 = mkstemp()
        select([tmp1], tmp2)
        generate(tmp2, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
