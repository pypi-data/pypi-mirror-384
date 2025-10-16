import argparse
import sys
from typing import Any, Dict, List, Optional

from jira import Issue, JIRA

from rhjira import util


def getnames(data: str) -> Optional[List[Dict[str, str]]]:
    """Convert comma-separated string to list of name dictionaries."""
    if data.strip() == "":
        return None

    entries = []
    for item in data.split(","):
        entry = {"name": item.strip()}
        entries.append(entry)
    return entries


def clone_comments(jira: JIRA, source_issue: Issue, target_issue: Issue) -> None:
    """Clone comments from source issue to target issue."""
    if not source_issue.fields.comment:
        return

    print(f"Cloning {len(source_issue.fields.comment.comments)} comments...")
    for comment in source_issue.fields.comment.comments:
        comment_text = f"[Comment from {source_issue.key} by {comment.author.name}]\n\n{comment.body}" # noqa: E501
        try:
            util.addcomment(jira, target_issue.key, comment_text)
            util.rhjiratax()
        except Exception as e:
            print(f"Warning: Failed to clone comment: {e}")


def clone_attachments(jira: JIRA, source_issue: Issue, target_issue: Issue) -> None:
    """Clone attachments from source issue to target issue."""
    if not hasattr(source_issue.fields, 'attachment') or not source_issue.fields.attachment:
        return

    print(f"Cloning {len(source_issue.fields.attachment)} attachments...")
    for attachment in source_issue.fields.attachment:
        try:
            # Download attachment content
            attachment_content = jira.attachment(attachment.id)
            # Upload to new issue
            jira.add_attachment(target_issue, attachment_content, filename=attachment.filename)
            util.rhjiratax()
        except Exception as e:
            print(f"Warning: Failed to clone attachment '{attachment.filename}': {e}")


def clone(jira: JIRA) -> None:
    # Handle arguments
    sys.argv.remove("clone")
    parser = argparse.ArgumentParser(
        description="Clone a jira ticket on https://issues.redhat.com"
    )
    parser.add_argument(
        "--tickettype", type=str, help="Override ticket type (Bug, Story, Epic, etc.)"
    )
    parser.add_argument(
        "--summary", type=str, help="Override summary for the cloned ticket"
    )
    parser.add_argument(
        "--description", type=str, help="Override description for the cloned ticket"
    )
    parser.add_argument(
        "--components", type=str, help="Override components (comma-separated)"
    )
    parser.add_argument(
        "--labels", type=str, help="Override labels (comma-separated)"
    )
    parser.add_argument(
        "--assignee", type=str, help="Set assignee for the cloned ticket"
    )
    parser.add_argument(
        "--priority", type=str, help="Override priority for the cloned ticket"
    )
    parser.add_argument(
        "--with-comments", action="store_true", help="Clone comments from original ticket"
    )
    parser.add_argument(
        "--with-attachments", action="store_true", help="Clone attachments from original ticket"
    )
    parser.add_argument(
        "--project", type=str, help="Override target project (defaults to same as source)"
    )
    args, ticketIDs = parser.parse_known_args()

    if len(ticketIDs) != 1:
        print(f"Error: ticketID not clear or found: {ticketIDs}")
        sys.exit(1)
    source_ticket_id = ticketIDs[0]

    # Fetch the source ticket
    try:
        source_issue = util.getissue(jira, source_ticket_id)
    except Exception as e:
        util.handle_jira_error(e, f"lookup source ticket {source_ticket_id}")
        sys.exit(1)

    # Prepare fields for the new ticket
    fields: Dict[str, Any] = {}

    # Project (use override or source project)
    if args.project:
        fields["project"] = {"key": args.project}
    else:
        fields["project"] = {"key": source_issue.fields.project.key}

    # Issue type (use override or source type)
    if args.tickettype:
        fields["issuetype"] = {"name": args.tickettype}
    else:
        fields["issuetype"] = {"name": source_issue.fields.issuetype.name}

    # Summary (use override or source summary with "Clone of" prefix)
    if args.summary:
        fields["summary"] = args.summary
    else:
        fields["summary"] = f"Clone of {source_issue.key}: {source_issue.fields.summary}"

    # Epic Name (required for Epics)
    if fields["issuetype"]["name"] == "Epic":
        fields["customfield_12311141"] = fields["summary"]

    # Description (use override or source description with clone note)
    if args.description:
        fields["description"] = args.description
    else:
        clone_note = f"[Cloned from {source_issue.key}]\n\n"
        original_description = source_issue.fields.description or ""
        fields["description"] = clone_note + original_description

    # Components (use override or source components)
    if args.components:
        fields["components"] = getnames(args.components)
    elif source_issue.fields.components:
        fields["components"] = [{"name": comp.name} for comp in source_issue.fields.components]

    # Labels (use override or source labels)
    if args.labels:
        fields["labels"] = [label.strip() for label in args.labels.split(",")]
    elif hasattr(source_issue.fields, 'labels') and source_issue.fields.labels:
        fields["labels"] = source_issue.fields.labels

    # Assignee (use override or leave unassigned)
    if args.assignee:
        fields["assignee"] = {"name": args.assignee}

    # Priority (use override or source priority)
    if args.priority:
        fields["priority"] = {"name": args.priority}
    elif source_issue.fields.priority:
        fields["priority"] = {"name": source_issue.fields.priority.name}

    # Copy other relevant fields from source
    # Epic Name (if source is Epic and target is Epic)
    if (source_issue.fields.issuetype.name == "Epic" and
        fields["issuetype"]["name"] == "Epic" and
        hasattr(source_issue.fields, 'customfield_12311141') and
        source_issue.fields.customfield_12311141):
        fields["customfield_12311141"] = f"Clone of {source_issue.fields.customfield_12311141}"

    # Epic Link (if source has one and target is not Epic)
    if (fields["issuetype"]["name"] != "Epic" and
        hasattr(source_issue.fields, 'customfield_12311140') and
        source_issue.fields.customfield_12311140):
        fields["customfield_12311140"] = source_issue.fields.customfield_12311140

    # Affects Versions
    if hasattr(source_issue.fields, 'versions') and source_issue.fields.versions:
        fields["versions"] = [{"name": version.name} for version in source_issue.fields.versions]

    # Fix Versions
    if hasattr(source_issue.fields, 'fixVersions') and source_issue.fields.fixVersions:
        fields["fixVersions"] = [{"name": version.name} for version in source_issue.fields.fixVersions] # noqa: E501

    # Contributors
    if (hasattr(source_issue.fields, 'customfield_12315950') and
        source_issue.fields.customfield_12315950):
        fields["customfield_12315950"] = [{"name": contrib.name} for contrib in source_issue.fields.customfield_12315950] # noqa: E501

    # Release Blocker
    if (hasattr(source_issue.fields, 'customfield_12319743') and
        source_issue.fields.customfield_12319743):
        fields["customfield_12319743"] = {"value": source_issue.fields.customfield_12319743.value}

    # Severity
    if (hasattr(source_issue.fields, 'customfield_12316142') and
        source_issue.fields.customfield_12316142):
        fields["customfield_12316142"] = {"value": source_issue.fields.customfield_12316142.value}

    # Create the new ticket
    try:
        print(f"Cloning {source_ticket_id} to new {fields['issuetype']['name']}...")
        new_issue = util.createissue(jira, fields)
        print(f"Successfully created: https://issues.redhat.com/browse/{new_issue.key}")

        # Clone comments if requested
        if getattr(args, 'with_comments', False):
            clone_comments(jira, source_issue, new_issue)

        # Clone attachments if requested
        if getattr(args, 'with_attachments', False):
            clone_attachments(jira, source_issue, new_issue)


    except Exception as e:
        project_key = fields.get("project", {}).get("key")
        util.handle_jira_error(e, "clone ticket", project_key)
        sys.exit(1)
