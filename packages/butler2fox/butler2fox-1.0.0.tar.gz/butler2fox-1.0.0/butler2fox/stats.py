import re

from butler2fox.jenkins import model as jk


def count_lines(jenkinsfile: str, model: jk.Pipeline) -> int:
    # compute lines of code
    sanitized = jenkinsfile
    # remove all comments
    sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.MULTILINE | re.DOTALL)
    sanitized = re.sub(r"^ *\/\/.*$", "", sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r"^ *#.*$", "", sanitized, flags=re.MULTILINE)
    # remove lines containing only code structuration and whitespaces
    sanitized = re.sub(r"^[ \(\)\{\}\[\]]*\n", "", sanitized, flags=re.MULTILINE)
    return sanitized.count("\n")
