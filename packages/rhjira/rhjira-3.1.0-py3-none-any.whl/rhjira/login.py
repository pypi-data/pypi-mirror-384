import getpass
import os
import sys
from typing import Optional

from jira import JIRA, JIRAError
import keyring

from rhjira import util

MAX_RETRIES = 6


def connect2jira(server: str, token: str) -> JIRA:
    last_error: Optional[JIRAError] = None
    for attempt in range(1, MAX_RETRIES):
        try:
            jira = JIRA(server=server, token_auth=token)
            jira.myself()  # test to see if this works
            util.rhjiratax()
            return jira
        except JIRAError as e:
            if attempt == (MAX_RETRIES - 1):
                print(
                    "Error: login failure.  This is likely caused by an invalid token.  Please verify your token and try again." # noqa: E501
                )
                util.handle_jira_error(e, "login")
                sys.exit(1)

    if last_error:
        print("ERROR: unknown login error")
    sys.exit(1)  # Fallback exit if we somehow get here


def login() -> JIRA:
    # check the keyring first
    token: Optional[str] = None
    try:
        token = keyring.get_password("rhjira", getpass.getuser())
    except Exception:
        pass

    if token is None or token == "":
        token = os.getenv("JIRA_TOKEN")
        if token is None or token == "":
            print("Error: The keyring password could not be read and JIRA_TOKEN was not set.")
            sys.exit(1)

    return connect2jira("https://issues.redhat.com", token)


def setpassword() -> None:
    token = getpass.getpass("Enter in token (hit ENTER to abort):")
    if token.strip() == "":
        print("No token entered ... aborting")
        sys.exit(1)

    username = getpass.getuser()
    print(f"Attempting to save token to {username}'s keyring ....")
    keyring.set_password("rhjira", username, token)
    print("testing login with token ....")

    login()

    print(f"Login succeeded.  Token is saved in keyring as ('{username}' on 'rhjira').")
