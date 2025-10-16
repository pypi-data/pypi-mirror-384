import argparse
from datetime import datetime
import re
import sys
from typing import Optional, Sequence, Union

from jira import Issue, JIRA
from jira.resources import Resource, User, Version

from rhjira import util


def getnames(fieldlist: Optional[Sequence[Union[Resource, User, Version]]]) -> str:
    retstr = ""
    count = 0
    if fieldlist:
        for entry in fieldlist:
            count += 1
            retstr = retstr + f"{entry.name}"
            if count != len(fieldlist):
                retstr = retstr + ", "
    return retstr


def defaultShowText(jira: JIRA, issue: Issue) -> str:
    epicname = ""
    epiclink = ""
    parentlink = ""

    if issue.fields.issuetype is not None:
        if issue.fields.issuetype.name == "Epic":
            epicname = issue.fields.customfield_12311141
            parentlink = issue.fields.customfield_12313140
            parentlink = "" if parentlink is None else parentlink
        else:
            epiclink = issue.fields.customfield_12311140
            epiclink = "" if epiclink is None else epiclink

    components = getnames(issue.fields.components)
    affectsversions = getnames(issue.fields.versions)
    fixversions = getnames(issue.fields.fixVersions)
    contributors = getnames(issue.fields.customfield_12315950)

    releaseblocker = ""
    if hasattr(issue.fields, 'customfield_12319743') and issue.fields.customfield_12319743:
        releaseblocker = issue.fields.customfield_12319743.value

    severity = ""
    if issue.fields.customfield_12316142:
        severity = issue.fields.customfield_12316142.value

    summarystatus = ""
    if issue.fields.issuetype.name in ["Feature", "Epic"]:
        if hasattr(issue.fields, 'customfield_12320841') and issue.fields.customfield_12320841:
            summarystatus = issue.fields.customfield_12320841

    gitpullrequest = ""
    if issue.fields.customfield_12310220:
        for url in issue.fields.customfield_12310220:
            gitpullrequest = url
            break

    assignee = ""
    if issue.fields.assignee is not None:
        assignee = issue.fields.assignee.name

    # Get blocking relationships
    blocks = []
    isblockedby = []
    if hasattr(issue.fields, 'issuelinks'):
        for link in issue.fields.issuelinks:
            if hasattr(link, 'outwardIssue'):
                summary = link.outwardIssue.raw.get('fields', {}).get('summary', '')
                status = link.outwardIssue.raw.get('fields', {}).get('status', {}).get('name', '')
                status_category = link.outwardIssue.raw.get('fields', {}).get('status', {}).get('statusCategory', {}).get('name', '')
                if link.type.outward == 'blocks':
                    blocks.append((link.outwardIssue.key, summary, status, status_category))
            if hasattr(link, 'inwardIssue'):
                summary = link.inwardIssue.raw.get('fields', {}).get('summary', '')
                status = link.inwardIssue.raw.get('fields', {}).get('status', {}).get('name', '')
                status_category = link.inwardIssue.raw.get('fields', {}).get('status', {}).get('statusCategory', {}).get('name', '')
                if link.type.inward == 'is blocked by':
                    isblockedby.append((link.inwardIssue.key, summary, status, status_category))

    # Initialize child_issues
    child_issues = []
    # Get child issues for Features and Epics
    if issue.fields.issuetype.name in ["Feature", "Epic"]:
        child_issues = util.searchissues(jira, f"'Parent Link' = {issue.key}", 2000)

    # Get Epic Link and Parent Link summaries
    epiclink_summary = ""
    epiclink_status = ""
    epiclink_category = ""
    parentlink_summary = ""
    parentlink_status = ""
    parentlink_category = ""
    if epiclink:
        try:
            epic = util.getissue(jira, epiclink)
            epiclink_summary = epic.fields.summary
            epiclink_status = epic.fields.status.name
            epiclink_category = epic.fields.status.statusCategory.name
        except Exception:
            pass
    if parentlink:
        try:
            parent = util.getissue(jira, parentlink)
            parentlink_summary = parent.fields.summary
            parentlink_status = parent.fields.status.name
            parentlink_category = parent.fields.status.statusCategory.name
        except Exception:
            pass

    status = issue.fields.status
    # Display resolution if status is Closed
    if status.name == "Closed" and issue.fields.resolution is not None:
        status = f"{status} ({issue.fields.resolution.name})"

    # Build the output lines
    lines = [
        f"{issue.key}: {issue.fields.summary}",
        "===================================",
        f"{issue.fields.description}",
        "===================================",
        f"Epic Name: {epicname}",
        f"Ticket Type: {issue.fields.issuetype}",
        f"Status: {status}",
        f"Creator: {issue.fields.creator.name}",
        f"Assignee: {assignee}",
        f"Components: {components}",
        f"Affects Versions: {affectsversions}",
        f"Fix Versions: {fixversions}",
        f"Priority: {issue.fields.priority.name}",
        f"Contributors: {contributors}",
        f"Release Blocker: {releaseblocker}",
        f"Severity: {severity}",
        f"Status Summary: {summarystatus}",
        f"Git Pull Request: {gitpullrequest}",
    ]

    # Add Epic Link if it exists
    if epiclink:
        lines.append(f"Epic Link: {util.format_link(epiclink, epiclink_summary, epiclink_status, epiclink_category)}")

    # Add Parent Link if it exists
    if parentlink:
        lines.append(f"Parent Link: {util.format_link(parentlink, parentlink_summary, parentlink_status, parentlink_category)}")

    # Add Blocks if they exist
    if blocks:
        lines.extend(f"Blocks: {util.format_link(key, summary, status, status_category)}" for key, summary, status, status_category in blocks)

    # Add Is Blocked By if they exist
    if isblockedby:
        lines.extend(f"Is Blocked By: {util.format_link(key, summary, status, status_category)}" for key, summary, status, status_category in isblockedby)

    # Add Child Issues if they exist
    if child_issues:
        lines.extend(f"Child Issue: {util.format_link(child.key, child.fields.summary, child.fields.status.name, child.fields.status.statusCategory.name)}" for child in child_issues)

    # Filter out empty lines and join with newlines
    return "\n".join(line for line in lines if line.strip())


def show(jira: JIRA) -> None:
    # handle arguments
    sys.argv.remove("show")
    parser = argparse.ArgumentParser(
        description="Show basic information on a RH jira ticket"
    )
    parser.add_argument(
        "--nocomments",
        action="store_true",
        help="Do not display comments for the ticket"
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

    outtext = defaultShowText(jira, issue)
    if issue.fields.issuetype.name == "Epic":
        outtext = re.sub(r"^Epic Link:.*\n?", "", outtext, flags=re.MULTILINE)
    else:
        outtext = re.sub(r"^Epic Name:.*\n?", "", outtext, flags=re.MULTILINE)
        outtext = re.sub(r"^Parent Link:.*\n?", "", outtext, flags=re.MULTILINE)

    if issue.fields.issuetype.name not in ["Bug", "Story"]:
        outtext = re.sub(r"^Git Pull Request:.*\n?", "", outtext, flags=re.MULTILINE)

    if issue.fields.issuetype.name not in ["Feature", "Epic"]:
        outtext = re.sub(r"^Status Summary:.*\n?", "", outtext, flags=re.MULTILINE)

    print(outtext)

    if args.nocomments:
        return

    if not issue.fields.comment:
        return

    numcomments = len(issue.fields.comment.comments)
    print(f"--------- {numcomments}  Comments ---------")

    count = 0
    for comment in issue.fields.comment.comments:
        count += 1
        created = datetime.strptime(comment.created, "%Y-%m-%dT%H:%M:%S.%f%z")
        print(f"Comment #{count} | {created.strftime('%c')} | {comment.author.name}")
        print("")
        print(f"{comment.body}")
        print("")
