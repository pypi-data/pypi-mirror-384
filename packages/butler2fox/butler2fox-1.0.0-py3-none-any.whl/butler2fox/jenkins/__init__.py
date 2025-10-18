import sys

from butler2fox.color import YELLOW
from butler2fox.jenkins import ast
from butler2fox.jenkins.model import JenkinsModelBuilder, Pipeline


def parse(jenkinsfile: any, filename: str = None, debug=False) -> Pipeline:
    tree = ast.parse(jenkinsfile, filename)
    if debug:
        print(YELLOW("Parsed Jenkins AST:"), file=sys.stderr)
        print(f"{tree.tree_str()}", file=sys.stderr)

    pipeline = tree.visit(JenkinsModelBuilder())
    if debug:
        print(YELLOW("Parsed Jenkins Model:"), file=sys.stderr)
        print(f"{pipeline}", file=sys.stderr)

    return pipeline
