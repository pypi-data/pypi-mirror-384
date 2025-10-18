#!/usr/bin/env python3

import argparse
import math
import sys
from pathlib import Path
from typing import TextIO

import butler2fox.color as color
from butler2fox import jenkins, migrator, stats


def cli_migrate(args):
    # 1: load and parse Jenkinsfile
    jenkinsfile = args.input.read()
    filename = args.input.name
    pipeline = jenkins.parse(jenkinsfile, filename, args.debug)

    # 2: convert to GitLab pipeline
    opts = migrator.Options(
        job_naming_convention=args.naming_convention,
    )
    pipeline, ctx = migrator.migrate_pipeline(pipeline, opts, args.debug)

    # 3: output result
    output: TextIO = args.output
    if output is None:
        # implicit output from input
        if args.input == sys.stdin:
            output = sys.stdout
        else:
            # TextIOWrapper from argparse
            intput_dir = Path(args.input.name).parent
            output_file = intput_dir / ".gitlab-ci.yml"
            output = open(output_file, "w")
    print(f"❯ Output to: {color.BLUE(output.name)}", file=sys.stderr)
    pipeline.dump(output)

    # 4: compute stats
    total_lines = stats.count_lines(jenkinsfile, pipeline)
    converted_lines = total_lines - ctx.not_migrated_lines
    conversion_ratio = float(converted_lines) / float(total_lines)
    cl: color
    if conversion_ratio < 0.5:
        cl = color.RED
    elif conversion_ratio < 0.7:
        cl = color.YELLOW
    else:
        cl = color.GREEN
    print(
        f"❯ Convertion rate: {cl(str(math.ceil(100.0 * conversion_ratio)) + '%')} ({converted_lines}/{total_lines} lines)",
        file=sys.stderr,
    )


def cli():
    parser = argparse.ArgumentParser(
        description="This tool can be used to migrate your Jenkins pipelines to GitLab CI/CD",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debugging",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.set_defaults(func=cli_migrate)
    parser.add_argument(
        "-i",
        "--input",
        help="Input Jenkinsfile (default: stdin)",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output GitLab CI YAML file (default: same dir as input or stdout)",
        type=argparse.FileType("w"),
        default=None,
    )
    parser.add_argument(
        "-nc",
        "--naming-convention",
        help="Jobs and stages naming convention (one of 'unchanged', 'snake', 'kebab', 'camel' or 'pascal')",
        type=migrator.NamingConvention,
        default=migrator.NamingConvention.unchanged,
    )

    # parse command and args
    args = parser.parse_args()
    # disable colouring on flag '--no-color'
    if args.no_color:
        # global COLORED_OUTPUT
        color.COLORED_OUTPUT = False
    args.func(args)


if __name__ == "__main__":
    cli()
