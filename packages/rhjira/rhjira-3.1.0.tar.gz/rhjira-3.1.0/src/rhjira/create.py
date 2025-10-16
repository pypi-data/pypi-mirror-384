import argparse
from datetime import datetime
import os
import sys
from typing import Any, Dict, List, Optional

from jira import JIRA

from rhjira import util


# ruff: noqa: E501
def getnames(data: str) -> Optional[List[Dict[str, str]]]:
    if data.strip() == "":
        return None

    entries = []
    for item in data.split(","):
        entry = {"name": item.strip()}
        entries.append(entry)
    return entries


def create(jira: JIRA) -> None:
    # handle arguments
    sys.argv.remove("create")
    parser = argparse.ArgumentParser(
        description="Create a jira ticket on https://issues.redhat.com"
    )
    parser.add_argument("--affectsversion", type=str, help="Affected Version.")
    parser.add_argument(
        "--assignee", type=str, help="Assignee email address used in RH Jira."
    )
    parser.add_argument(
        "--components", type=str, help="Components (must be specified)."
    )
    parser.add_argument(
        "--contributors",
        type=str,
        help="Contributors (comma separated list of email addresses).",
    )
    parser.add_argument("--description", type=str, help="Description for the ticket.")
    parser.add_argument("--epiclink", type=str, help="Epic Link")
    parser.add_argument("--epicname", type=str, help="Epic Name")
    parser.add_argument("--fixversion", type=str, help="Fix/Versions.")
    parser.add_argument(
        "--noeditor",
        action="store_true",
        help="when set the editor will not be invoked",
    )
    parser.add_argument("--parentlink", type=str, help="Parent Link")
    parser.add_argument("--priority", type=str, help="Priority, Normal by default.")
    parser.add_argument(
        "--project", type=str, help="Project Name (RHEL, RHELAI, AIPCC, etc.)."
    )
    parser.add_argument("--releaseblocker", type=str, help="Release Blocker Status.")
    parser.add_argument("--severity", type=str, help="Severity Level.")
    parser.add_argument(
        "--summary",
        type=str,
        help="Summary for the ticket.  Cannot exceed more than one line.",
    )
    parser.add_argument(
        "-T",
        "--template",
        type=str,
        help="Create jira with template file (will be opened in $GITLAB_EDITOR)",
    )
    parser.add_argument(
        "--tickettype", type=str, help="Ticket Type (Epic, Story, Bug, etc.)."
    )
    parser.add_argument(
        "--isblockedby", type=str, help="issue which blocks this new issue"
    )
    parser.add_argument(
        "--blocks", type=str, help="issue that is blocked by this new issue"
    )
    args = parser.parse_args()

    # clear unset vars
    for arg in vars(args):
        if getattr(args, arg) is None:
            setattr(args, arg, "")

    # The description is a special case.  If it's been passed on the command line with a \n,
    # then we need to parse this so it looks like real text.
    description = util.convertdescription(args.description)

    defaultCreateText = f"""# Please fill out the following fields.  This file can be saved to create a template.
# Project (RHEL, RHELAI, AIPCC, RHELENG, etc.)
Project: {args.project}
# Ticket Type (Epic, Bug, Story, etc.)
Ticket Type: {args.tickettype}
# Epic Name (required if Ticket Type is Epic, o/w ignored)
Epic Name: {args.epicname}
# Summary (one line only)
Summary: {args.summary}
# Description (multi line accepted)
# Note: all 'free' lines in text file will be accepted as part of the Description
Description: {description}
# Assignee (email address)
Assignee: {args.assignee}
# Components (case sensitive)
Components: {args.components}
# Affects Versions
Affects Versions: {args.affectsversion}
# Fix Version
Fix Version: {args.fixversion}
# Priority
Priority: {args.priority}
#
# The fields below may not be available on all projects.
#
# Contributors (comma separated list of email addresses)
Contributors: {args.contributors}
# Release Blocker (default to None)
Release Blocker: {args.releaseblocker}
# Severity
Severity: {args.severity}
# Epic Link
Epic Link: {args.epiclink}
# Parent Link
Parent Link: {args.parentlink}
# Is Blocked By
Is Blocked By: {args.isblockedby}
# Blocks
Blocks: {args.blocks}
"""

    createtext = defaultCreateText
    if args.template != "":
        try:
            with open(args.template, "r") as file:
                createtext = file.read()
        except Exception as error:
            print(f"Unable to open {args.template}: {error}")
            sys.exit(1)

    if not args.noeditor:
        createtext = util.editFile("rhjira", createtext)

    if len(createtext) == 0:
        print("No text found ... aborting.")
        sys.exit(1)

    fields: Dict[str, Any] = {}
    description = ""
    isblockedby = ""
    blocks = ""
    for line in createtext.splitlines():
        token = line.split(":")[0] + ":"
        data = line[len(token) + 1 :].strip()

        match token:
            case "Project:":
                fields["project"] = {"key": data.strip()}
            case "Ticket Type:":
                tickettype = data.strip()
                fields["issuetype"] = {"name": data.strip()}
            case "Epic Name:":
                if tickettype == "Epic":
                    fields["customfield_12311141"] = data.strip()
            case "Summary:":
                fields["summary"] = data.strip()
            case "Description:":
                description = data.strip()
            case "Assignee:":
                if data != "":
                    fields["assignee"] = {"name": data}
            case "Components:":
                if data != "":
                    fields["components"] = getnames(data)
            case "Affects Versions:":
                if data != "":
                    fields["versions"] = getnames(data)
            case "Fix Version:":
                if data != "":
                    fields["fixVersions"] = getnames(data)
            case "Priority:":
                if data != "":
                    fields["priority"] = {"name": data.strip()}
            case "Contributors:":
                if data != "":
                    fields["customfield_12315950"] = getnames(data)
            case "Release Blocker:":
                if data != "":
                    fields["customfield_12319743"] = {"value": data}
            case "Severity:":
                if data != "":
                    fields["customfield_12316142"] = {"value": data}
            case "Epic Link:":
                if data != "" and tickettype != "Epic":
                    fields["customfield_12311140"] = data.strip()
            case "Parent Link:":
                if data != "" and tickettype == "Epic":
                    fields["customfield_12313140"] = data.strip()
            case "Is Blocked By:":
                if data != "":
                    isblockedby = data.strip()
            case "Blocks:":
                if data != "":
                    blocks = data.strip()
            case _:
                description = description + "\n" + line

    fields["description"] = description

    try:
        issue = util.createissue(jira, fields)
        # Create issue links if specified
        if isblockedby:
            util.createissuelink(
                jira,
                'Blocks',  # Link type is always "Blocks"
                isblockedby,  # The blocking issue is the inward issue
                issue.key,  # The blocked issue is the outward issue
                fields["project"]["key"]  # Project key for error messages
            )
        if blocks:
            util.createissuelink(
                jira,
                'Blocks',  # Link type is always "Blocks"
                issue.key,  # The blocking issue is the inward issue
                blocks,  # The blocked issue is the outward issue
                fields["project"]["key"]  # Project key for error messages
            )
        print(f"https://issues.redhat.com/browse/{issue.key}")
    except Exception:
        # Error has already been handled and displayed by retry_jira_operation
        tmpdir = os.environ.get("TMPDIR")
        if tmpdir is None:
            tmpdir = "/tmp"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        try:
            with open(f"{tmpdir}/rhjira.{timestamp}", "w") as file:
                file.write(createtext)
                file.close()
        except Exception as error:
            print(f"Unable to save error template file to {tmpdir}/rhjira.{timestamp}: {error}")
            sys.exit(1)
        filepath = f"{tmpdir}/rhjira.{timestamp}"

        print(
            f"To re-run the command with the existing options execute 'rhjira create -T {filepath}'"
        )
        sys.exit(1)
