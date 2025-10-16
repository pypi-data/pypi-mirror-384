from datetime import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import time
from typing import (
    Any,
    Callable,
    cast,
    Dict,
    List,
    Optional,
    overload,
    Protocol,
    Sequence,
    TypeVar,
    Union,
)

from jira import Issue, JIRA, JIRAError
from jira.resources import (
    Attachment,
    Comment,
    Component,
    Group,
    IssueLink,
    Resource,
    SecurityLevel,
    User,
    Version,
    Votes,
    Watchers,
)

from rhjira import login


# Custom type definitions for missing Jira types
class BugzillaBug(Protocol):
    bugid: str


class JiraOption(Protocol):
    value: str
    child: Optional["JiraOption"]


class JiraProgress(Protocol):
    progress: int


class JiraNamedResource(Protocol):
    name: str


# Type variables for generic functions
T = TypeVar("T", bound=Resource)
StrConvertible = Union[str, int, float, bool, None]

MAX_RETRIES = 6


def convertdescription(description: str) -> str:
    return description.replace(r"\n", "\n")


def dumpissue(issue: Issue) -> None:
    print(json.dumps(issue.raw, indent=4))


def rhjiratax() -> None:
    # RH's Jira instance has a 2/second/node rate limit.  To avoid
    # this the code has to implement a half second delay at times.

    # PRARIT: I've tested this with .25 seconds, and it doesn't make a
    # difference.  The test run takes 2700 vs 2600 seconds to run.
    time.sleep(.5)


def removecomments(intext: str) -> str:
    # remove all lines beginning with # (hash)
    outtext = re.sub(r"^#.*\n", "", intext, flags=re.MULTILINE)
    return outtext


def isGitRepo() -> bool:
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.check_call(
                ["git", "-C", "./", "rev-parse", "--is-inside-work-tree"],
                stdout=devnull,
                stderr=devnull,
            )
        return True
    except subprocess.CalledProcessError:
        return False


def geteditor() -> str:
    editor = os.environ.get("GIT_EDITOR") or os.environ.get("EDITOR") or "vi"
    if not editor:
        print("Could not determine editor.  Please set GIT_EDITOR or EDITOR.")
        sys.exit(1)

    return editor


def editFile(fileprefix: str, message: Optional[str]) -> str:
    editor = geteditor()
    command = shlex.split(editor)

    if isGitRepo():
        workingdir = os.getcwd()
    else:
        workingdir = "/tmp"

    filename = workingdir + "/" + f"{fileprefix}_EDITMSG"

    command.append(filename)

    # prepopulate the file with message
    if message:
        with open(filename, "w") as file:
            file.write(message)

    # open the editor and save the contents in $filename
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Editor open failed with: {e}")
        os.remove(filename)
        sys.exit(1)

    # read the saved contents of $filename
    with open(filename, "r") as file:
        intext = file.read()

    # cleanup
    os.remove(filename)

    intext = removecomments(intext)
    intext = re.sub(r"^#.*\n", "", intext, flags=re.MULTILINE)

    return intext


@overload
def dump_any(field: Resource, value: None) -> str: ...


@overload
def dump_any(field: Resource, value: Union[str, int, float, bool]) -> str: ...


@overload
def dump_any(field: Resource, value: Any) -> str: ...


def dump_any(field: Resource, value: Any) -> str:
    if value is None:
        return ""
    # customfield_12316840/"Bugzilla Bug"
    if field.id == "customfield_12316840" and hasattr(value, "bugid"):
        bug = cast(BugzillaBug, value)
        return str(bug.bugid)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if hasattr(value, "name"):
        named_resource = cast(JiraNamedResource, value)
        return str(named_resource.name)
    return str(value)


def dump_user(field: Resource, user: User) -> str:
    return f"{user.displayName} <{user.emailAddress}>"


def dump_version(field: Resource, version: Version) -> str:
    return str(version.name)


def dump_component(field: Resource, component: Component) -> str:
    return str(component.name)


def dump_issuelink(field: Resource, issuelink: IssueLink) -> str:
    if hasattr(issuelink, "outwardIssue"):
        return f"{issuelink.type.outward} https://issues.redhat.com/browse/{issuelink.outwardIssue.key}"
    return f"{issuelink.type.inward} https://issues.redhat.com/browse/{issuelink.inwardIssue.key}"


def dump_attachment(field: Resource, attachment: Attachment) -> str:
    return str(attachment.content)


def dump_group(field: Resource, group: Group) -> str:
    return str(group.name)


def dump_array(field: Resource, array: Sequence[Any]) -> str:
    # customfield_12323140/"Target Version"
    if field.id == "customfield_12323140":
        return dump_version(field, cast(Version, array))
    # customfield_12315950/"Contributors"
    if field.id == "customfield_12315950":
        userstr = ""
        count = 0
        for cf in array:
            count += 1
            user = cast(User, cf)
            userstr = userstr + dump_user(field, user)
            if count != len(array):
                userstr = userstr + ", "
        return userstr

    if not array:
        return ""

    if field.schema["items"] and field.schema["items"] != "worklog":
        retstr = ""
        count = 0
        for entry in array:
            count += 1
            match field.schema["items"]:
                case "attachment":
                    retstr = retstr + dump_attachment(field, cast(Attachment, entry))
                case "component":
                    retstr = retstr + dump_component(field, cast(Component, entry))
                case "group":
                    retstr = retstr + dump_group(field, cast(Group, entry))
                case "issuelinks":
                    retstr = retstr + dump_issuelink(field, cast(IssueLink, entry))
                case "option":
                    retstr = retstr + dump_option(field, cast(JiraOption, entry))
                case "string":
                    retstr = retstr + str(entry)
                case "user":
                    retstr = retstr + dump_user(field, cast(User, entry))
                case "version":
                    retstr = retstr + dump_version(field, cast(Version, entry))
                case "worklog":
                    return ""
                case _:
                    print(f"PRARIT unhandled array {field.schema['items']}")
                    return ""
            if count != len(array):
                retstr = retstr + ", "
        return retstr

    return ""


def dump_securitylevel(field: Resource, security: SecurityLevel) -> str:
    return str(security.description)


def dump_option(field: Resource, option: JiraOption) -> str:
    return str(option.value)


def dump_optionwithchild(field: Resource, option: JiraOption) -> str:
    if hasattr(option, "child") and option.child:
        return f"{option.value} - {option.child.value}"
    return str(option.value)


def dump_votes(field: Resource, votes: Votes) -> int:
    return int(votes.votes)


def dump_progress(field: Resource, progress: JiraProgress) -> str:
    return f"{progress.progress}%"


def dump_watches(field: Resource, watches: Watchers) -> str:
    if not watches.isWatching:
        return "0"
    return str(watches.watchCount)


def dump_comment(field: Resource, comment: Comment) -> str:
    creator = dump_user(field, comment.author)
    timestamp = convert_jira_date(comment.created)
    return f'"Created by {creator} at {timestamp} :\\n{comment.body}\\n\\n"'


def dump_comments(field: Resource, comments: List[Comment]) -> str:
    retstr = ""
    count = 0
    for comment in comments:
        count += 1
        retstr = retstr + dump_comment(field, comment)
        if count != len(comments):
            retstr = retstr + ", "
    return retstr


def convert_jira_date(datestr: str) -> str:
    try:
        # 2024-09-03 11:34:05
        date = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        # 2025-04-30
        try:
            date = datetime.strptime(datestr, "%Y-%m-%d")
        except Exception:
            print(f"ERROR: undefined date format {datestr}")
            sys.exit(1)
    return date.strftime("%Y-%m-%d %H:%M:%S")


def dict_to_struct(data: Dict[str, Any]) -> Resource:
    return cast(Resource, type("", (object,), data)())


def evaluatefield(field: Resource, value: Any, noescapedtext: bool) -> Optional[Union[str, int]]:
    schema = dict_to_struct(field.schema)
    match schema.type:
        case "any":
            # "Git Pull Request"
            if field.id == "customfield_12310220":
                retstr = ""
                count = 0
                for v in value:
                    count += 1
                    retstr = retstr + str(v)
                    if count != len(value):
                        retstr += ", "
                return retstr
            return str(dump_any(field, value))
        case "array":
            if value is None:
                return ""
            return str(dump_array(field, value))
        case "date":
            if value is None:
                return ""
            return str(convert_jira_date(value))
        case "datetime":
            if value is None:
                return ""
            date = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
            return date.strftime("%Y-%m-%d %H:%M:%S")
        case "issuelinks":
            if value is None:
                return ""
            return str(dump_issuelink(field, cast(IssueLink, value)))
        case "issuetype":
            return str(value)
        case "number":
            if value is None:
                return "0"
            return int(float(value))
        case "sd-approvals":
            return ""
        case "sd-customerrequesttype":
            return ""
        case "sd-servicelevelagreement":
            return ""
        case "securitylevel":
            if value is None:
                return ""
            return str(dump_securitylevel(field, cast(SecurityLevel, value)))
        case "string":
            if value is None:
                return ""
            if noescapedtext:
                return str(value)
            return str(value).replace("\n", "\\n")
        case "timetracking":
            return ""
        case "option":
            if value is None:
                return ""
            return str(dump_option(field, cast(JiraOption, value)))
        case "option-with-child":
            if value is None:
                return ""
            return str(dump_optionwithchild(field, cast(JiraOption, value)))
        case "priority":
            if value is None:
                return ""
            return str(value)
        case "project":
            if value is None:
                return ""
            return str(value)
        case "progress":
            if value is None:
                return ""
            return str(dump_progress(field, cast(JiraProgress, value)))
        case "resolution":
            if value is None:
                return ""
            return str(value)
        case "status":
            if value is None:
                return ""
            return str(value)
        case "user":
            if value is None:
                return ""
            return str(dump_user(field, cast(User, value)))
        case "version":
            if value is None:
                return ""
            return str(dump_version(field, cast(Version, value)))
        case "votes":
            if value is None:
                return ""
            return int(dump_votes(field, cast(Votes, value)))
        case "watches":
            if value is None:
                return ""
            return str(dump_watches(field, cast(Watchers, value)))
        case "comments-page":
            return str(dump_comments(field, value.comments))
        case _:
            print(
                f"ERROR undefined field type FIELD[{field.name}|{field.id}]: ",
                schema.type,
                value,
            )
            return None


def getfieldlist(
    jirafields: List[Dict[str, Any]], userfields: Optional[List[str]]
) -> List[Resource]:
    # generate a list of fields
    fields: List[Resource] = []
    if not userfields:
        for fielddict in jirafields:
            field = dict_to_struct(fielddict)
            fields.append(field)
        return fields

    for userfield in userfields:
        for fielddict in jirafields:
            field = dict_to_struct(fielddict)
            if field.id == userfield or field.name == userfield:
                fields.append(field)
                continue
    return fields


MAX_RETRIES = 5


class RHJiraFetchError(Exception):
    pass


def _get_issue(jira: JIRA, ticketID: str) -> Issue:
    for attempt in range(1, MAX_RETRIES):
        try:
            issue = jira.issue(ticketID)
            rhjiratax()
            return issue
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def getissue(jira: JIRA, ticketID: str) -> Issue:
    return cast(Issue, retry_jira_operation(_get_issue, jira, ticketID))


def _get_fields(jira: JIRA) -> List[Dict[str, Any]]:
    for attempt in range(1, MAX_RETRIES):
        try:
            fields = jira.fields()
            rhjiratax()
            return fields
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def getfields(jira: JIRA) -> List[Dict[str, Any]]:
    return cast(List[Dict[str, Any]], retry_jira_operation(_get_fields, jira))


def _add_comment(jira: JIRA, ticketID: str, savedText: str) -> None:
    for attempt in range(1, MAX_RETRIES):
        try:
            jira.add_comment(ticketID, savedText)
            rhjiratax()
            return
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def addcomment(jira: JIRA, ticketID: str, savedText: str) -> None:
    retry_jira_operation(_add_comment, jira, ticketID, savedText)


def _create_issue(jira: JIRA, fields: Dict[str, Any]) -> Issue:
    for attempt in range(1, MAX_RETRIES):
        try:
            issue = jira.create_issue(fields=fields)
            rhjiratax()
            return issue
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def createissue(jira: JIRA, fields: Dict[str, Any]) -> Issue:
    project_key = fields.get("project", {}).get("key")
    return cast(Issue,
                retry_jira_operation(_create_issue,
                                     jira,
                                     fields,
                                     additional_info=project_key)
                )

def _get_resolutions(jira: JIRA, issue: Issue) -> List[Dict[str, Any]]:
    for attempt in range(1, MAX_RETRIES):
        try:
            resolutions = jira.resolutions()
            rhjiratax()
            return [r.raw for r in resolutions]
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def _get_transitions(jira: JIRA, issue: Issue) -> List[Dict[str, Any]]:
    for attempt in range(1, MAX_RETRIES):
        try:
            transitions = jira.transitions(issue)
            rhjiratax()
            return list(transitions)
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def gettransitions(jira: JIRA, issue: Issue) -> List[Dict[str, Any]]:
    return cast(List[Dict[str, Any]], retry_jira_operation(_get_transitions, jira, issue))


def _transition_issue(jira: JIRA, issue: Issue, stateID: str, resolution: str) -> None:
    fields: Dict[str, Any] = {}
    if resolution is not None:
        fields["resolution"] = {"name": resolution}

    for attempt in range(1, MAX_RETRIES):
        try:
            jira.transition_issue(issue, stateID, fields)
            rhjiratax()
            return
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def transitionissue(jira: JIRA, issue: Issue, stateID: str, resolution: str) -> None:
    res = None
    if resolution is not None:
        resolutions = _get_resolutions(jira, issue)
        for r in resolutions:
            if r["name"] == resolution:
                res = r["name"]
                break
        if res is None:
            raise ValueError(f"Resolution '{resolution}' not found in project")

    retry_jira_operation(_transition_issue, jira, issue, stateID, res)


def _assign_issue(jira: JIRA, issue: Issue, assignee: Optional[str]) -> None:
    for attempt in range(1, MAX_RETRIES):
        try:
            jira.assign_issue(issue, assignee)
            rhjiratax()
            return
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def assignissue(jira: JIRA, issue: Issue, assignee: Optional[str]) -> None:
    retry_jira_operation(_assign_issue, jira, issue, assignee)


def _search_issues(jira: JIRA, searchstring: str, maxentries: int) -> List[Issue]:
    for attempt in range(1, MAX_RETRIES):
        try:
            issues = jira.search_issues(searchstring, maxResults=maxentries)
            rhjiratax()
            return cast(List[Issue], list(issues))
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def searchissues(jira: JIRA, searchstring: str, maxentries: int) -> List[Issue]:
    return cast(List[Issue], retry_jira_operation(_search_issues, jira, searchstring, maxentries))


def _create_issue_link(jira: JIRA, linktype: str, inwardissue: str, outwardissue: str) -> None:
    for attempt in range(1, MAX_RETRIES):
        try:
            jira.create_issue_link(
                type=linktype,
                inwardIssue=inwardissue,
                outwardIssue=outwardissue
            )
            rhjiratax()
            return
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                raise RHJiraFetchError(f"JIRAError {e.status_code}: {e.text}") from e
    raise RHJiraFetchError("Maximum retries exceeded")


def createissuelink(
    jira: JIRA,
    linktype: str,
    inwardissue: str,
    outwardissue: str,
    project_key: Optional[str] = None
) -> None:
    retry_jira_operation(_create_issue_link,
                         jira,
                         linktype,
                         inwardissue,
                         outwardissue,
                         additional_info=project_key)


def is_resolution_error(e: Exception) -> bool:
    return isinstance(e, ValueError) and str(e).startswith("Resolution ")


def handle_jira_error(e: Exception, context: str, additional_info: Optional[str] = None) -> bool:
    # Accept both direct JIRAError and wrapped in __cause__
    jira_error = None
    if isinstance(e, JIRAError):
        jira_error = e
    elif hasattr(e, '__cause__') and isinstance(e.__cause__, JIRAError):
        jira_error = e.__cause__

    if jira_error:
        try:
            # Defensive: response may be None
            resp_text = getattr(jira_error.response, 'text', None)
            if resp_text is not None:
                resp = json.loads(resp_text)
            else:
                resp = {}
            print(f"Failed to {context}: {getattr(jira_error, 'status_code', 'Unknown')}")
            if "errorMessages" in resp:
                for msg in resp["errorMessages"]:
                    print(f"Error: {msg}")
            if "errors" in resp:
                for field, error in resp["errors"].items():
                    print(f"     Field '{field}': {error}")
                    if field == "components" and "is not valid" in str(error):
                        print(
                            f"     Run 'rhjira info --project {additional_info} components' to see valid component names" # noqa: E501
                        )
                    if field == "versions" and "is not valid" in str(error):
                        print(
                            f"     Run 'rhjira info --project {additional_info} versions' to see valid version names" # noqa: E501
                        )
                    if field == "fixVersions" and "is not valid" in str(error):
                        print(
                            f"     Run 'rhjira info --project {additional_info} versions' to see valid version names" # noqa: E501
                        )
                    if field == "resolutions" and "is not valid" in str(error) and additional_info:
                        print(
                            f"     Run 'rhjira info --project {additional_info} resolutions' to see valid resolution names" #noqa: E501
                        )
            if additional_info:
                print(additional_info)
            # Return True if this was a 401 authentication error
            return getattr(jira_error, 'status_code', None) == 401
        except json.JSONDecodeError:
            print(f"Failed to {context}: {getattr(jira_error, 'status_code', 'Unknown')} {getattr(jira_error, 'text', '')}") #noqa: E501
            return getattr(jira_error, 'status_code', None) == 401
    else:
        print(f"Failed to {context}: {e}")
        return False


def retry_jira_operation(
    operation: Callable[..., Any],
    *args: Any,
    additional_info: Optional[str] = None,
    **kwargs: Any
) -> Any:
    """
    Retry a JIRA operation with authentication retry on 401 errors.

    Args:
        operation: The JIRA operation function to retry
        *args: Arguments to pass to the operation
        additional_info: Additional information to pass to error handler (e.g., project key)
        **kwargs: Keyword arguments to pass to the operation

    Returns:
        The result of the operation if successful

    Raises:
        Exception: If the operation fails after all retries
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            # Check if this was an authentication error
            if handle_jira_error(e, "perform JIRA operation", additional_info):
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Authentication failed, retrying ({retry_count}/{max_retries})...")
                    # Re-authenticate by creating a new JIRA client
                    new_jira = login.login()

                    # Replace the old client with the new one in the args tuple
                    args = (new_jira,) + args[1:]

                    # Update the global jira reference in the calling module
                    import inspect
                    frame = inspect.currentframe()
                    if frame and frame.f_back:
                        caller_frame = frame.f_back
                        if 'jira' in caller_frame.f_globals:
                            caller_frame.f_globals['jira'] = new_jira

                    continue
            # If not an auth error or we're out of retries, re-raise
            raise


def format_link(key: str, summary: str, status: str, status_category: str) -> str:
    """Format a JIRA issue link with color-coded status."""
    # Determine color based on status category
    if not status_category:
        color = "\033[34m"  # Default to blue if no category
    elif status_category == "To Do":
        color = "\033[90m"  # Light grey
    elif status_category == "Done":
        color = "\033[32m"  # Green
    else:
        color = "\033[34m"  # Blue

    return f'\033]8;;https://issues.redhat.com/browse/{key}\a{key}\033]8;;\a\033[0;37m {summary} ({color}{status}\033[0m)' # noqa: E501
