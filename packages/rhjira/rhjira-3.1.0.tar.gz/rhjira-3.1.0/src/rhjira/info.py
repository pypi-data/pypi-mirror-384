import sys
from typing import Any

from jira import JIRA, JIRAError

from rhjira import util


def get_project_info(jira: JIRA, project_key: str, info_type: str) -> list[dict[str, Any]]:
    try:
        if info_type == "components":
            components = jira.project_components(project_key)
            return [{"name": c.name} for c in components]
        elif info_type == "resolutions":
            # Resolutions are global, not per-project, but for consistency, we fetch them here
            resolutions = jira.resolutions()
            return [{"name": r.name, "description": getattr(r, "description", "")} for r in resolutions] # noqa: E501
        else:  # versions
            versions = jira.project_versions(project_key)
            return [{"name": v.name} for v in versions]
    except JIRAError as e:
        util.handle_jira_error(e, f"fetch {info_type} for project {project_key}")
        sys.exit(1)


def display_components(components: list[dict[str, Any]]) -> None:
    if components:
        for c in components:
            print(c["name"])
    else:
        print("No components found.")


def display_versions(versions: list[dict[str, Any]]) -> None:
    if versions:
        for v in versions:
            print(v["name"])
    else:
        print("No versions found.")


def display_resolutions(resolutions: list[dict[str, Any]]) -> None:
    if resolutions:
        for r in resolutions:
            desc = f" - {r['description']}" if r.get('description') else ""
            print(f"{r['name']}{desc}")
    else:
        print("No resolutions found.")


def info(jira: JIRA) -> None:
    # handle arguments
    sys.argv.remove("info")

    if len(sys.argv) != 4 or sys.argv[1] != "--project":
        print("Usage: rhjira info --project <project> <components|versions|resolutions>")
        sys.exit(1)

    project = sys.argv[2]
    info_type = sys.argv[3]

    if info_type not in ["components", "versions", "resolutions"]:
        print("Error: info type must be either 'components', 'versions', or 'resolutions'")
        sys.exit(1)

    info_list = get_project_info(jira, project, info_type)

    if info_type == "components":
        display_components(info_list)
    elif info_type == "versions":
        display_versions(info_list)
    else:
        display_resolutions(info_list)
