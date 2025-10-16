"""Display JIRA ticket hierarchy."""

import argparse
import sys

from jira import Issue, JIRA

from rhjira import util


def display_hierarchy(jira: JIRA, issue: Issue, indent: int = 0, expand: bool = False) -> None:
    """Display the hierarchy of a JIRA ticket, including child issues and blocking relationships."""
    # Format the current issue
    indent_str = "        " * indent
    if indent == 0:  # Only show the full issue info for the root issue
        print(f"{indent_str}{issue.fields.issuetype.name}: {util.format_link(issue.key, issue.fields.summary, issue.fields.status.name, issue.fields.status.statusCategory.name)}")

    # Get blocking relationships
    if hasattr(issue.fields, 'issuelinks'):
        for link in issue.fields.issuelinks:
            if hasattr(link, 'inwardIssue') and link.type.inward == 'is blocked by':
                blocked_by_key = link.inwardIssue.key
                try:
                    blocked_by = util.getissue(jira, blocked_by_key)
                    print(f"{indent_str}        Is Blocked By: {blocked_by.fields.issuetype.name}: {util.format_link(blocked_by.key, blocked_by.fields.summary, blocked_by.fields.status.name, blocked_by.fields.status.statusCategory.name)}")
                    # Recursively display blocking issue's hierarchy only if expand is True
                    if expand:
                        display_hierarchy(jira, blocked_by, indent + 1, expand)
                except Exception:
                    # If we can't get the full issue, just show what we have
                    print(f"{indent_str}        Is Blocked By: {util.format_link(blocked_by_key, link.inwardIssue.fields.summary, link.inwardIssue.fields.status.name, link.inwardIssue.fields.status.statusCategory.name)}")

    # Get child issues
    child_issues = util.searchissues(jira, f"'Parent Link' = {issue.key}", 2000)
    for child in child_issues:
        print(f"{indent_str}        {child.fields.issuetype.name}: {util.format_link(child.key, child.fields.summary, child.fields.status.name, child.fields.status.statusCategory.name)}")
        # Recursively display child's hierarchy
        display_hierarchy(jira, child, indent + 1, expand)


def hierarchy(jira: JIRA) -> None:
    """Display the hierarchy of a JIRA ticket."""
    # handle arguments
    sys.argv.remove("hierarchy")
    parser = argparse.ArgumentParser(
        description="Show hierarchy information for a RH jira ticket"
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand blocking issues to show their full hierarchy (default: only show blocking ticket summary)"
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

    display_hierarchy(jira, issue, expand=args.expand)
