rhjira-python is a utility and library that provides functionality to interact with Red Hat's Jira, https://issues.redhat.com.  The functionality in this project currently supports creating, editing, commenting on, and the displaying of jiras.

Token Configuration

rhjira-python requires a Jira Token (https://issues.redhat.com/secure/ViewProfile.jspa).  The token can be exported as JIRA_TOKEN, however it is recommended users execute 'rhjira settoken' to store their token in their keyring.  This is more secure than keeping the token in clear text and using JIRA_TOKEN.

Tokens can be removed from the keyring by simply removing the 'rhjira' entry.  In the commonly used seahorse application, this can be done by removing the 'Password for '{username}' on 'rhjira'' entry.

Help

All commands are supported via --help.  For example, to get help on the comment command, execute "rhjira comment --help".

Problems found with rhjira-python can be reported at https://gitlab.com/prarit/rhjira-python/-/issues.  As with all my projects, merge requests are welcomed!

Bugs with rhjira should include the version of rhjira you are running and the exact executed command that failed.
