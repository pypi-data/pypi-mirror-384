import argparse
import re
import sys
from typing import Any, Dict, List, Match

from jira import JIRA
from tabulate import tabulate

from rhjira import util


def list(jira: JIRA) -> None:
    # handle arguments
    sys.argv.remove("list")
    parser = argparse.ArgumentParser(description="list issues")
    parser.add_argument(
        "--fields", type=str, help="specify a comma-separated list of fields for output"
    )
    parser.add_argument(
        "--numentries", type=int, help="maximum number of entries to return"
    )
    parser.add_argument(
        "--summarylength",
        type=int,
        help="Length of the summary string (default:50, do not truncate:0)",
    )
    parser.add_argument(
        "--noheader", action="store_true", help="do not display an output header"
    )
    parser.add_argument(
        "--nolinenumber", action="store_true", help="do not display leading line number"
    )
    parser.add_argument(
        "--rawoutput",
        action="store_true",
        help="do not make output pretty (useful for scripts)",
    )
    parser.add_argument(
        "--textonly",
        action="store_true",
        help="do not output URLs",
    )
    args, jqls = parser.parse_known_args()

    if len(jqls) != 1:
        print("Error: No search string provided.")
        sys.exit(1)
    jqlstring = jqls[0]

    try:
        jirafields = util.getfields(jira)
    except Exception as e:
        util.handle_jira_error(e, "lookup fields")
        sys.exit(1)

    # replace 'customfield' with actual name (for example, Constributors)
    lookup: Dict[str, str] = {item["id"]: item["name"] for item in jirafields}

    def replace_cf(match: Match[str]) -> str:
        key = match.group(0)
        return lookup.get(key, key)

    searchstring = re.sub(r"\bcustomfield_\d+\b", replace_cf, jqlstring)

    maxentries = args.numentries if args.numentries else 50

    try:
        issues = util.searchissues(jira, searchstring, maxentries)
        util.rhjiratax()
    except Exception as e:
        util.handle_jira_error(e, "search")
        sys.exit(1)

    if not issues:  # This handles both None and empty list cases
        print("No issues found.")
        sys.exit(0)

    # default is to show the issue key and the summary
    userfields: List[str] = ["key", "summary"]
    if args.fields:
        userfields = args.fields.split(",")
        # issue key is always output
        if "key" not in userfields:
            userfields.insert(0, "key")

    # generate a list of fields
    fields = util.getfieldlist(jirafields, userfields)

    data: List[List[Any]] = []
    count = 0
    issuekeyindex = 0  # used in table output
    for issue in issues:
        entry: List[Any] = []

        if not args.nolinenumber:
            issuekeyindex = 1
            entry.append(count)

        entry.append(issue.key)

        for field in fields:
            try:
                value = getattr(issue.fields, field.id)
                if field.custom and value is None:
                    entry.append("---")
                    continue
            except Exception:
                entry.append("---" if field.custom else "")
                continue

            # this seems strange, but I want the evaluatefield outside of
            # a try/except.  Otherwise, errors in evaluatefield get 'caught'
            entry.append(util.evaluatefield(field, value, False))

        data.append(entry)
        count += 1

    # issue.key is displayed as "Issue" in the first column
    userfields[0] = "Issue"

    if not args.nolinenumber:
        userfields.insert(0, "#")

    if args.rawoutput:
        for entry in data:
            print(*entry, sep="|")
        return

    if args.noheader:
        print(tabulate(data, tablefmt="plain"))
    else:
        tableoutput = tabulate(data, headers=userfields, tablefmt="plain")

        if args.textonly:
            print(tableoutput)
            sys.exit(1)

        # tabulate uses the full string length to calculate column widths.
        # This causes weird table output when using the full URL length (see
        # below).  Instead, just search/replace the issuekey.
        for line in tableoutput.splitlines():
            issuekey = line.split()[issuekeyindex]
            print(
                line.replace(
                    issuekey,
                    f"\033]8;;https://issues.redhat.com/browse/{issuekey}\a{issuekey}\033]8;;\a\033[0;37m",
                )
            )
