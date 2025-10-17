"""
Find solution/program/package/module version from single source of truth (SSoT)

SSoT can be:
- some pyproject.toml file which has version number inside and that number is official because it is published
- ??
"""

import toml # pip install toml
from loguru import logger

def version_from_pyproject_file(file_name: str) -> str:
    """
    Returns key "version" value from section "project" from TOML-formatted input file. 
    On errors returns unknown (empty string).
    """
    unknown: str = ""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            toml_string = f.read()
    except: # whatever is wrong we act same way:
        logger.error(f"Cannot load the file {file_name}")
        return unknown
    return version_from_pyproject_toml_string(toml_string)


def version_from_pyproject_toml_string(toml_string: str) -> str:
    """
    Returns key "version" value from section "project". 
    On errors returns unknown (empty string).
    """
    unknown: str = ""
    try:
        parsed_toml: dict = toml.loads(toml_string)
        project_version = parsed_toml.get("project", {}).get("version", None)
        if project_version is None:
            logger.error(f"No version info from TOML")
            return unknown
    except:
        logger.error(f"Input is not a TOML formatted string")
        return unknown
    logger.debug(f"Got version - {project_version}")
    return project_version


def do_tests():
    assert 1 == 1
    #assert version_from_pyproject_file(r"../deployfiles/pyproject.toml") == "0.0.3" # this wouldn't work after first legal change of pyproject.toml file
    assert version_from_pyproject_file(r"../nofile.toml") == ""
    assert version_from_pyproject_toml_string("""[project]\nname = "whatever"\nversion = "2.31.3"\n """) == "2.31.3"
    assert version_from_pyproject_toml_string("""[project]\nname = "whatever"\nversion = "452.131.53-dev1"\n """) == "452.131.53-dev1"
    assert version_from_pyproject_toml_string("""[projecrsion = "2.31.3"\n """) == ""
    assert version_from_pyproject_toml_string("""[project]\nname = "whatever"\n """) == ""
    print("--> tests were succesful")


if __name__ == "__main__":
    do_tests()
