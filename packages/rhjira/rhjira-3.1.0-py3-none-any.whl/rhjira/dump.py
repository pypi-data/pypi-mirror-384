import argparse
import sys
from typing import Optional, Union

from jira import JIRA
from jira.resources import Resource

from rhjira import util

showcustomfields = True


def outputfield(field: Resource, data: Optional[Union[str, int]]) -> None:
    if showcustomfields:
        if data is None or data == "":
            print(f"FIELD[{field.name}|{field.id}]:")
        else:
            print(f"FIELD[{field.name}|{field.id}]: {data}")
    else:
        if data is None or data == "":
            print(f"FIELD[{field.name}]:")
        else:
            print(f"FIELD[{field.name}]: {data}")


noescapedtext = True


def dump(jira: JIRA) -> None:
    # handle arguments
    sys.argv.remove("dump")
    parser = argparse.ArgumentParser(description="Dump jira issue variables.")
    parser.add_argument(
        "--fields", type=str, help="specify a comma-separated list of fields for output"
    )
    parser.add_argument(
        "--noescapedtext",
        action="store_true",
        help="show dump text (ie, no escaped characters)",
    )
    parser.add_argument(
        "--showcustomfields",
        action="store_true",
        help="show the customfield IDs and the customfield names",
    )
    parser.add_argument(
        "--showemptyfields",
        action="store_true",
        help="show all fields including those that are not defined for this issue",
    )
    parser.add_argument("--json", action="store_true", help="dump issue in json format")
    args, ticketIDs = parser.parse_known_args()

    if len(ticketIDs) != 1:
        print(f"Error: ticketID not clear or found: {ticketIDs}")
        sys.exit(1)
    ticketID = ticketIDs[0]

    userfields = args.fields
    if args.fields and len(args.fields) != 0:
        userfields = args.fields.split(",")
    global noescapedtext
    noescapedtext = args.noescapedtext
    global showcustomfields
    showcustomfields = args.showcustomfields
    showemptyfields = args.showemptyfields

    try:
        issue = util.getissue(jira, ticketID)
    except Exception as e:
        util.handle_jira_error(e, f"lookup ticket {ticketID}")
        sys.exit(1)

    if args.json:
        util.dumpissue(issue)
        sys.exit(0)

    try:
        jirafields = util.getfields(jira)
    except Exception as e:
        util.handle_jira_error(e, "lookup fields")
        sys.exit(1)

    fields = util.getfieldlist(jirafields, userfields)

    # output the fields
    for field in fields:
        if field.id in issue.raw["fields"]:
            if issue.raw["fields"][field.id]:
                try:
                    value = getattr(issue.fields, field.id)
                except AttributeError:
                    value = ""

                outputfield(field, util.evaluatefield(field, value, noescapedtext))
            else:
                if showemptyfields:
                    outputfield(field, "")
        else:
            # For some reason the issue key field is not populated with a value.
            if field.id == "issuekey":
                outputfield(field, ticketID)
                continue
            if showemptyfields:
                outputfield(field, "")
