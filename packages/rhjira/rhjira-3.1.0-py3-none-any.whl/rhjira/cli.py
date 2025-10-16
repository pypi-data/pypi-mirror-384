import sys
from typing import NoReturn

from jira import JIRAError

import rhjira
from rhjira import util


def usage() -> NoReturn:
    print("Usage:")
    print("  rhjira [flags] [command]")
    print(" ")
    print("Available Commands:")
    print("  clone       Clone a jira ticket on https://issues.redhat.com")
    print("  comment     Comment on a jira ticket on https://issues.redhat.com")
    print("  create      Create a jira ticket on https://issues.redhat.com")
    print("  dump        Dump jira issue variables.")
    print("  edit        Edit a jira ticket on https://issues.redhat.com")
    print("  help        Help about any command")
    print("  hierarchy   Show hierarchy information for a jira ticket")
    print("  info        Display project information (components and versions)")
    print("  list        List issues")
    print(
        "  settoken    Save a jira token to the keyring (more secure than using $JIRA_TOKEN)"
    )
    print("  show        Show a jira ticket on https://issues.redhat.com")
    print(" ")
    print("For help on individual commands, execute rhjira [command] --help")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) <= 1:
        usage()

    if sys.argv[1] != "settoken":
        try:
            jira = rhjira.login()
        except JIRAError as e:
            util.handle_jira_error(e, "login")
            sys.exit(1)

    match sys.argv[1]:
        case "clone":
            rhjira.clone(jira)
        case "comment":
            rhjira.comment(jira)
        case "close":
            rhjira.edit(jira)
        case "create":
            rhjira.create(jira)
        case "dump":
            rhjira.dump(jira)
        case "edit":
            rhjira.edit(jira)
        case "info":
            rhjira.info(jira)
        case "list":
            rhjira.list(jira)
        case "settoken":
            rhjira.setpassword()
        case "show":
            rhjira.show(jira)
        case "hierarchy":
            rhjira.hierarchy(jira)
        case _:
            usage()


if __name__ == "__main__":
    main()
