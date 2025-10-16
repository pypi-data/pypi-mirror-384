import argparse
import sys
from typing import Any, Dict, List, Optional, Sequence

from jira import Issue, JIRA, JIRAError
from jira.resources import Resource

from rhjira import util


def transitionissue(jira: JIRA, issue: Issue, newstatus: str, resolution: str) -> None:
    if issue.fields.status.name == newstatus and newstatus != "Closed":
        print(f"issue {issue.key} is already {newstatus}")
        sys.exit(0)

    try:
        transitions = util.gettransitions(jira, issue)
    except Exception as e:
        util.handle_jira_error(e, f"lookup transitions for {issue.key}")
        sys.exit(1)

    for transition in transitions:
        # according to Jira documentation, the newstatus status must exist.
        if transition["name"] == newstatus:
            try:
                util.transitionissue(jira, issue, transition["id"], resolution)
                # note, rhjiratax must be handled on caller side
                return
            except Exception as e:
                util.handle_jira_error(e, f"transition to {newstatus} for {issue.key}")
                sys.exit(1)
    print(f"Failed to find status '{newstatus}' for project {issue.fields.project.key}")
    sys.exit(1)


def string2entries(data: str) -> Optional[List[Dict[str, str]]]:
    if data.strip() == "":
        return None

    entries = []
    for item in data.split(","):
        entry = {"name": item.strip()}
        entries.append(entry)
    return entries


def entries2string(data: Optional[Sequence[Resource]]) -> str:
    retstr = ""

    if data is None:
        return retstr

    count = 0
    for item in data:
        count += 1
        retstr = retstr + item.name
        if count < len(data):
            retstr = retstr + ", "
    return retstr


def edit(jira: JIRA) -> None:
    # handle arguments
    closejira = False
    if "close" in sys.argv:
        closejira = True
        sys.argv.remove("close")

    if "edit" in sys.argv:
        sys.argv.remove("edit")

    parser = argparse.ArgumentParser(
        description="Create a jira ticket on https://issues.redhat.com"
    )
    parser.add_argument(
        "--affectsversion", type=str, default=None, help="Affected Version."
    )
    parser.add_argument(
        "--assignee",
        type=str,
        default=None,
        help="Assignee email address used in RH Jira.",
    )
    parser.add_argument(
        "--close", action="store_true", help="Close Ticket/Set status to 'Closed'"
    )
    parser.add_argument(
        "--components", type=str, default=None, help="Components (must be specified)."
    )
    parser.add_argument(
        "--contributors",
        type=str,
        default=None,
        help="Contributors (comma separated list of email addresses).",
    )
    parser.add_argument(
        "--description", type=str, default=None, help="Description for the ticket."
    )
    parser.add_argument("--epiclink", type=str, default=None, help="Epic Link")
    parser.add_argument("--epicname", type=str, default=None, help="Epic Name")
    parser.add_argument("--fixversion", type=str, default=None, help="Fix/Versions.")
    parser.add_argument(
        "--gitpullrequest", type=str, default=None, help="Git Pull Request"
    )
    parser.add_argument(
        "--noeditor",
        action="store_true",
        help="when set the editor will not be invoked",
    )
    parser.add_argument("--parentlink", type=str, default=None, help="Parent Link")
    parser.add_argument(
        "--priority", type=str, default=None, help="Priority, Normal by default."
    )
    parser.add_argument(
        "--releaseblocker", type=str, default=None, help="Release Blocker Status."
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Status (New, In Progress, Review, Closed, etc.)",
    )
    parser.add_argument("--severity", type=str, default=None, help="Severity Level.")
    parser.add_argument(
        "--summary",
        type=str,
        default=None,
        help="Summary for the ticket.  Cannot exceed more than one line.",
    )
    parser.add_argument(
        "--isblockedby", type=str, default=None, help="issue which blocks this issue"
    )
    parser.add_argument(
        "--blocks", type=str, default=None, help="issue that is blocked by this issue"
    )
    parser.add_argument(
        "--resolution", type=str, default=None, help="why the issue was marked Closed"
    )
    parser.add_argument(
        "--summarystatus", type=str, default=None, help="Status Summary field"
    )
    args, ticketIDs = parser.parse_known_args()

    if len(ticketIDs) != 1:
        print(f"Error: ticketID not clear or found: {ticketIDs}")
        sys.exit(1)
    ticketID = ticketIDs[0]

    try:
        issue = util.getissue(jira, ticketID)
    except Exception as e:
        util.handle_jira_error(e, f"lookup ticket {ticketID}")
        sys.exit(1)

    # if 'close' is specified, just close the Jira and return
    if closejira:
        transitionissue(jira, issue, "Closed", args.resolution)
        print(f"Closed https://issues.redhat.com/browse/{ticketID}")
        sys.exit(0)

    # clear unset vars
    # for arg in vars(args):
    #    if getattr(args, arg) is None:
    #        setattr(args, arg, "")

    epicname = ""
    if issue.fields.issuetype.name == "Epic":
        epicname = issue.fields.customfield_12311141
    if args.epicname is not None:
        epicname = args.epicname

    summary = issue.fields.summary
    if args.summary is not None:
        summary = args.summary

    description = issue.fields.description
    if args.description is not None:
        description = args.description

    assignee = ""
    if issue.fields.assignee is not None:
        assignee = issue.fields.assignee.name
    if args.assignee is not None:
        assignee = args.assignee

    components = entries2string(issue.fields.components)
    if args.components is not None:
        components = args.components

    affectsversion = entries2string(issue.fields.versions)
    if args.affectsversion is not None:
        affectsversion = args.affectsversion

    fixversion = entries2string(issue.fields.fixVersions)
    if args.fixversion is not None:
        fixversion = args.fixversion

    priority = issue.fields.priority.name
    if args.priority is not None:
        priority = args.priority

    contributors = entries2string(issue.fields.customfield_12315950)
    if args.contributors is not None:
        contributors = args.contributors

    releaseblocker = ""
    if issue.fields.customfield_12319743 is not None:
        releaseblocker = issue.fields.customfield_12319743
    if args.releaseblocker is not None:
        releaseblocker = args.releaseblocker

    severity = ""
    if issue.fields.customfield_12316142 is not None:
        severity = issue.fields.customfield_12316142
    if args.severity is not None:
        severity = args.severity

    summarystatus = ""
    if issue.fields.issuetype.name in ["Feature", "Epic"]:
        if (hasattr(issue.fields, 'customfield_12320841') and
            issue.fields.customfield_12320841 is not None):
            summarystatus = issue.fields.customfield_12320841
        if args.summarystatus is not None:
            summarystatus = args.summarystatus

    isblockedby = ""
    if args.isblockedby is not None:
        isblockedby = args.isblockedby

    blocks = ""
    if args.blocks is not None:
        blocks = args.blocks

    epiclink = ""
    if (
        issue.fields.issuetype.name != "Epic"
        and issue.fields.customfield_12311140 is not None
    ):
        epiclink = issue.fields.customfield_12311140
    if args.epiclink is not None:
        epiclink = args.epiclink

    parentlink = ""
    if (
        issue.fields.issuetype.name == "Epic"
        and issue.fields.customfield_12313140 is not None
    ):
        parentlink = issue.fields.customfield_12313140
    if args.parentlink is not None:
        parentlink = args.parentlink

    gitpullrequest = ""
    if issue.fields.issuetype.name in ["Bug", "Story"]:
        if issue.fields.customfield_12310220 is not None:
            gitpullrequest = ",".join(issue.fields.customfield_12310220)
    if args.gitpullrequest is not None:
        gitpullrequest = args.gitpullrequest

    status = issue.fields.status.name
    if args.status is not None:
        status = args.status

    resolution = args.resolution
    if resolution is None and issue.fields.resolution is not None:
        resolution = issue.fields.resolution.name

    # Due to the complexities of doing so, tickettype cannot be changed in the CLI.
    # This value is referenced while configuring fields.
    issuetype = issue.fields.issuetype.name

    # Build the Status Summary line only for Features and Epics
    summarystatus_line = ""
    if issuetype in ["Feature", "Epic"]:
        summarystatus_line = f"# Status Summary\nStatus Summary: {summarystatus}\n"

    defaultEditText = f"""# Edit {issuetype} {ticketID}. The following fields can be modified.
# Epic Name (required if Ticket Type is Epic, o/w ignored)
Epic Name: {epicname}
# Summary (one line only)
Summary: {summary}
# Status (New, In Progress, Closed, etc.)
Status: {status}
# Description (multi line accepted)
# Note: all 'free' lines in text file will be accepted as part of the Description
Description: {description}
# Assignee (email address)
Assignee: {assignee}
# Components (case sensitive)
Components: {components}
# Affects Versions
Affects Versions: {affectsversion}
# Fix Version
Fix Version: {fixversion}
# Priority
Priority: {priority}
#
# The fields below may not be available on all projects.
#
# Contributors (comma separated list of email addresses)
Contributors: {contributors}
# Release Blocker (default to None)
Release Blocker: {releaseblocker}
# Severity
Severity: {severity}
{summarystatus_line}# Epic Link
Epic Link: {epiclink}
# Parent Link
Parent Link: {parentlink}
# Git Pull Request
Git Pull Request: {gitpullrequest}
# Is Blocked By
Is Blocked By: {isblockedby}
# Blocks
Blocks: {blocks}
# Resolution (only valid when transitioning to Closed)
Resolution: {resolution}
"""

    edittext = ""
    if args.noeditor:
        edittext = util.removecomments(defaultEditText)
    else:
        origtext = util.removecomments(defaultEditText)
        edittext = util.editFile("rhjira", defaultEditText)

        user_set_args = [
            v for k, v in vars(args).items()
            if k not in ("noeditor",) and v not in (None, False, "", [])
        ]

        if origtext == edittext and not user_set_args:
            print("No changes made in editor.... aborting.")
            sys.exit(0)

    fields: Dict[str, Any] = {}
    description = ""
    for line in edittext.splitlines():
        token = line.split(":")[0] + ":"
        data = line[len(token) + 1 :].strip()

        match token:
            case "Project:":
                fields["project"] = {"key": data.strip()}
            case "Ticket Type:":
                fields["issuetype"] = {"name": data.strip()}
            case "Epic Name:":
                if issuetype == "Epic":
                    fields["customfield_12311141"] = data.strip()
            case "Summary:":
                fields["summary"] = data.strip()
            case "Description:":
                description = data.strip()
            case "Assignee:":
                # this requires different permissions than editing so it's a separate
                # jira call
                assignee = data.strip()
                if issue.fields.assignee is not None:
                    if assignee != issue.fields.assignee.name:
                        assignee = data.strip()

                if assignee == "":
                    assignee = None  # type: ignore
                try:
                    util.assignissue(jira, issue, assignee)
                    util.rhjiratax()
                except Exception as e:
                    util.handle_jira_error(e, "assign issue")
                    sys.exit(1)
            case "Components:":
                if data == "":
                    fields["components"] = []
                if data != "":
                    fields["components"] = string2entries(data)
            case "Affects Versions:":
                fields["versions"] = []
                if data != "":
                    fields["versions"] = string2entries(data)
            case "Fix Version:":
                fields["fixVersions"] = []
                if data != "":
                    fields["fixVersions"] = string2entries(data)
            case "Priority:":
                if data != "":
                    fields["priority"] = {"name": data.strip()}
            case "Contributors:":
                fields["customfield_12315950"] = []
                if data != "":
                    fields["customfield_12315950"] = string2entries(data)
            case "Release Blocker:":
                if data == "" and issue.fields.customfield_12319743 is None:
                    continue
                if data != "":
                    fields["customfield_12319743"] = {"value": data}
                else:
                    fields["customfield_12319743"] = None
            case "Severity:":
                if data != "":
                    fields["customfield_12316142"] = {"value": data}
            case "Status Summary:":
                if issuetype in ["Feature", "Epic"]:
                    if data != "":
                        fields["customfield_12320841"] = data
                    else:
                        fields["customfield_12320841"] = None
            case "Is Blocked By:":
                if data != "":
                    isblockedby = data.strip()
            case "Blocks:":
                if data != "":
                    blocks = data.strip()
            case "Epic Link:":
                if issuetype in ["Epic", "Feature"]:
                    continue
                if data != "":
                    fields["customfield_12311140"] = data.strip()
                else:
                    fields["customfield_12311140"] = None
            case "Parent Link:":
                if issuetype != "Epic":
                    continue
                fields["customfield_12313140"] = ""
                if data != "":
                    fields["customfield_12313140"] = data.strip()
            case "Git Pull Request:":
                if issuetype in ["Bug", "Story"]:
                    fields["customfield_12310220"] = ""
                    if data != "":
                        fields["customfield_12310220"] = f"{data}"
                    else:
                        fields["customfield_12310220"] = None
            case "Status:":
                status = data.strip()
            case "Resolution:":
                resolution = None
                if status == "Closed":
                    resolution = data.strip()
                    if resolution == "None":
                        resolution = "Done"
            case _:
                # this means every 'uncommented' line not in the case statements is
                # part of the description
                description = description + "\n" + line

    # The description is a special case.  If it's been passed on the command line with a \n,
    # then we need to parse this so it looks like real text.
    description = util.convertdescription(description)

    fields["description"] = description

    if issue.fields.status.name != status or status == "Closed":
        transitionissue(jira, issue, status, resolution)

    try:
        issue.update(fields=fields)
        # Create issue links if specified
        if isblockedby:
            util.createissuelink(
                jira,
                'Blocks',  # Link type is always "Blocks"
                isblockedby,  # The blocking issue is the inward issue
                issue.key  # The blocked issue is the outward issue
            )
        if blocks:
            util.createissuelink(
                jira,
                'Blocks',  # Link type is always "Blocks"
                issue.key,  # The blocking issue is the inward issue
                blocks  # The blocked issue is the outward issue
            )
        print(f"https://issues.redhat.com/browse/{ticketID}")
    except JIRAError as e:
        util.handle_jira_error(e, "update issue", issue.fields.project.key)
        sys.exit(1)
