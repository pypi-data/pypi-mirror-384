*** Settings ***
Documentation       Common Used Keywords for API Testing
...                 This resource file contains high-level keywords that build upon the API keywords.
...                 Keywords cover project setup, account management, file operations, and task execution.

Library             Collections
Library             DateTime
Library             OperatingSystem
Library             JSONLibrary
Library             RequestsLibrary
Library             ../libraries/utils.py


*** Keywords ***
Create Directory If Not Exists
    [Documentation]    Checks whether the specified directory exists, and creates it if it does not.
    ...
    ...    This keyword is useful for ensuring the presence of required folder structures
    ...    before logging, storing files, or initializing test environments.
    ...
    ...    Internally, it uses `Directory Should Exist` to check for existence and
    ...    `Create Directory` only if needed.
    ...
    ...    *Argument Details:*
    ...    - ``directory``: Path of the directory to check/create
    ...
    ...    *Example:*
    ...    | Create Directory If Not Exists | ${CONFIG_DIR} |
    [Arguments]    ${directory}
    ${dir_exists}    Run Keyword And Return Status    Directory Should Exist    ${directory}
    IF    not ${dir_exists}    Create Directory    ${directory}
    Log    Directory check completed for: ${directory}

Log Pretty JSON
    [Documentation]    Formats and logs a JSON payload with proper indentation for better readability.
    ...
    ...    *Arguments:*
    ...    - ``payload_name``: Name or label for the JSON payload in the log
    ...    - ``json_payload``: The JSON payload to format and log
    ...
    ...    *Example:*
    ...    | Log Pretty JSON | Task Configuration | ${task_payload} |
    [Arguments]    ${payload_name}    ${json_payload}
    ${pretty_json}    Evaluate    json.dumps($json_payload, indent=4)    modules=json
    Log    \n==== ✅ ${payload_name}- PAYLOAD ====\n${pretty_json}    level=CONSOLE

Wait Before Suite Execution
    [Documentation]    Pauses execution for a specified number of minutes before continuing suite execution.
    ...    This is typically used to wait for snaplex startup or other initialization processes.
    ...
    ...    *Arguments:*
    ...    - ``minutes``: Number of minutes to wait
    ...
    ...    *Example:*
    ...    | Wait Before Suite Execution | 3 |
    [Arguments]    ${minutes}
    Log    waitng for 3 minutes before test suite execution for snaplex to get started    level=CONSOLE
    Sleep    ${minutes}

Find Files With Pattern
    [Documentation]    Finds all files in a directory matching a given pattern
    ...
    ...    Supports wildcards for flexible file matching. Used internally by
    ...    upload keywords to handle pattern-based uploads.
    ...
    ...    *Arguments:*
    ...    - ``directory``: Directory path to search in
    ...    - ``pattern``: File pattern with optional wildcards
    ...
    ...    *Wildcard Support:*
    ...    - ``*`` matches zero or more characters
    ...    - ``?`` matches exactly one character
    ...
    ...    *Returns:*
    ...    - List of full paths to matching files
    ...
    ...    *Examples:*
    ...    | @{files} | Find Files With Pattern | /tmp/data | *.csv |
    ...    | @{logs} | Find Files With Pattern | /var/log | app_2025_??.log |
    ...    | @{configs} | Find Files With Pattern | /etc | config.* |
    ...
    ...    *Error Handling:*
    ...    - Fails if no files match the pattern
    ...    - Case-sensitive matching (depends on filesystem)
    [Arguments]    ${directory}    ${pattern}

    @{all_files}    List Files In Directory    ${directory}
    @{matching_files}    Create List

    FOR    ${file}    IN    @{all_files}
        ${matches}    Run Keyword And Return Status    Should Match    ${file}    ${pattern}
        IF    ${matches}
            ${full_path}    Set Variable    ${directory}/${file}
            Append To List    ${matching_files}    ${full_path}
        END
    END

    ${count}    Get Length    ${matching_files}
    Should Be True    ${count} > 0    No files found matching pattern: ${pattern} in ${directory}

    RETURN    ${matching_files}
