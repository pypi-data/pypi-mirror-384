*** Settings ***
Documentation       Common Used Keywords for API Testing
...                 This resource file contains keywords for API testing with RequestsLibrary.
...                 Keywords cover authentication, CRUD operations for projects, tasks, accounts and pipelines.

Library             RequestsLibrary
Library             JSONLibrary
Library             Collections
Library             String
Library             ../libraries/utils.py


*** Variables ***
${ORG_ADMIN_SESSION}        snaplogic-org-admin
${GLOBAL_ORG_SNODE_ID}      ${EMPTY}    # Global organization snode ID
${SESSION}                  snaplogic


*** Keywords ***
Login Api
    [Documentation]    Creates a session with authentication for API access.
    ...
    ...    This keyword creates an authenticated session for making API calls to the SnapLogic platform.
    ...    The session is created with the global session name and uses basic authentication.
    ...
    ...    *Arguments:*
    ...    - ``auth``: Authentication list containing [username, password] for session creation
    ...
    ...    *Returns:*
    ...    None (creates global session for subsequent API calls)
    ...
    ...    *Examples:*
    ...    | ${auth} = | Create List | myuser | mypassword |
    ...    | Login Api | ${auth} |
    ...    |
    ...    | # Alternative with variables |
    ...    | ${auth} = | Create List | ${USERNAME} | ${PASSWORD} |
    ...    | Login Api | ${auth} |
    ...
    ...    *Note:* Requires global variable ``${url}`` to be set with the base API URL
    ...
    ...    *See also:* `Get Auth Token`
    [Arguments]    ${auth}
    Create Session    ${ORG_ADMIN_SESSION}    ${url}    auth=${auth}    verify=true

Get Org List Api
    [Documentation]    Retrieves the list of assets for a specific organization.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Org List Api | my_organization |
    [Arguments]    ${org_name}
    ${resp}    GET On Session    ${ORG_ADMIN_SESSION}    /api/1/rest/asset/list/${org_name}
    RETURN    ${resp}

Get Project List Api
    [Documentation]    Retrieves the list of projects for a specific organization and project space.
    ...    Uses Handle API Error for comprehensive error handling.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Project List Api | my_organization | my_project_space |
    [Arguments]    ${org_name}    ${project_space}
    Log    project list api is: /api/1/rest/asset/list/${org_name}/${project_space}

    # Define the resource name for error reporting
    ${resource_name}    Set Variable    project list for ${org_name}/${project_space}

    # Use Try-Except to properly handle HTTP errors
    TRY
        # Use expected_status=anything to prevent automatic exception on non-200 responses
        ${resp}    GET On Session
        ...    ${ORG_ADMIN_SESSION}
        ...    /api/1/rest/asset/list/${org_name}/${project_space}
        ...    expected_status=anything

        # Log response details for debugging
        Log    GET Response: url=${resp.url} status=${resp.status_code}, reason=${resp.reason}

        # Check if there's an error in the response (status code >= 400)
        IF    ${resp.status_code} >= 400
            # Use Handle API Error to process the error response
            Handle API Error    ${resp}    ${resource_name}    retrieving
        END

        RETURN    ${resp}
    EXCEPT    AS    ${error}
        # Use Handle API Error to process exceptions
        Handle API Error    ${error}    ${resource_name}    retrieving    is_exception=True
    END

Create Project Space Api
    [Documentation]    Creates a new project space in the specified organization.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space to create
    ...    - ``payload``: JSON payload with project space details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Project Space Api | my_organization | my_project_space | ${payload} |
    [Arguments]    ${org_name}    ${project_space}    ${payload}
    ${params}    Create Dictionary    path=${org_name}/${project_space}
    ${resp}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/asset/${org_name}/${project_space}
    ...    params=${params}
    ...    json=${payload}
    RETURN    ${resp}

Create Project Api
    [Documentation]    Creates a new project in the specified organization and project space.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space
    ...    - ``project_name``: Name of the project to create
    ...    - ``payload``: JSON payload with project details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Project Api | my_organization | my_project_space | my_project | ${payload} |
    [Arguments]    ${org_name}    ${project_space}    ${project_name}    ${payload}
    ${params}    Create Dictionary    path=${org_name}/${project_space}/${project_name}
    ${resp}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/asset/${org_name}/${project_space}/${project_name}
    ...    params=${params}
    ...    json=${payload}
    RETURN    ${resp}

Delete Project Api
    [Documentation]    Soft-deletes a project in the specified organization and project space.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space
    ...    - ``project_name``: Name of the project to delete
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete Project Api | my_organization | my_project_space | my_project |
    [Arguments]    ${org_name}    ${project_space}    ${project_name}
    ${params}    Create Dictionary    soft_delete=True    asset_type=Dir
    ${resp}    DELETE On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/asset/${org_name}/${project_space}/${project_name}
    ...    params=${params}
    RETURN    ${resp}

Delete ProjectSpace Api
    [Documentation]    Soft-deletes a project space in the specified organization.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space to delete
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete ProjectSpace Api | my_organization | my_project_space |
    [Arguments]    ${org_name}    ${project_space}
    ${params}    Create Dictionary    soft_delete=True    asset_type=Dir

    TRY
        ${resp}    DELETE On Session
        ...    ${ORG_ADMIN_SESSION}
        ...    /api/1/rest/asset/${org_name}/${project_space}
        ...    params=${params}
        ...    expected_status=any

        # Check for error status code
        IF    ${resp.status_code} == 500
            ${json}    Evaluate    json.loads('''${resp.content}''')    json
            ${error_msg}    Set Variable    ${json['response_map']['error_list'][0]['message']}
            Log    Error deleting project space [${project_space}]: ${error_msg}    level=ERROR
            Fail    ${error_msg}
        END

        RETURN    ${resp}
    EXCEPT    AS    ${error}
        Log    Exception during DELETE operation: ${error}    level=ERROR
        Fail    Failed to delete project space [${project_space}]: ${error}
    END
    RETURN    ${resp}

GET Runtime Path Id Api
    [Documentation]    Retrieves runtime path ID for a specified organization.
    ...
    ...    *Arguments:*
    ...    - ``org_name_passed``: Name of the organization
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | GET Runtime Path Id Api | my_organization |
    [Arguments]    ${org_name_passed}    ${expected_status}=200
    ${params}    Create Dictionary    subscriber_id=${org_name_passed}
    ${resp}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    api/1/rest/slserver/snaplex_cc_details_with_info
    ...    params=${params}
    RETURN    ${resp}

Create Task Api Old
    [Documentation]    Creates a new task using the old API endpoint.
    ...
    ...    *Arguments:*
    ...    - ``payload``: JSON payload with task details
    ...    - ``duplicate_check``: Whether to check for duplicates (default: True)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Task Api Old | ${payload} | ${TRUE} |
    [Arguments]    ${payload}    ${duplicate_check}=True
    ${params}    Create Dictionary    duplicate_check=${duplicate_check}
    ${resp}    POST On Session    ${ORG_ADMIN_SESSION}    api/1/rest/slsched/job    json=${payload}
    ...    params=${params}
    RETURN    ${resp}

Get Accounts Detail Api
    [Documentation]    Retrieves detailed information about accounts in the organization.
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Accounts Detail Api |
    ${params}    Create Dictionary    org_path=${org_name}    level=detail
    ${resp}    GET On Session    ${ORG_ADMIN_SESSION}    api/1/rest/admin/snappack/catalog/accounts
    ...    params=${params}
    RETURN    ${resp}

Update Task Api
    [Documentation]    Updates an existing task with new parameters.
    ...
    ...    *Arguments:*
    ...    - ``task_snode_id``: The snode ID of the task to update
    ...    - ``payload``: JSON payload with updated task details
    ...    - ``duplicate_check``: Whether to check for duplicates (default: True)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Update Task Api | task_123 | ${payload} | ${TRUE} |
    [Arguments]    ${task_snode_id}    ${payload}    ${duplicate_check}=True
    ${params}    Create Dictionary    duplicate_check=${duplicate_check}
    ${resp}    PUT On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    api/1/rest/slsched/job/${task_snode_id}
    ...    json=${payload}
    ...    params=${params}
    RETURN    ${resp}

Get Account Api
    [Documentation]    Retrieves information about a specific account.
    ...
    ...    *Arguments:*
    ...    - ``account_id``: ID of the account to retrieve
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Account Api | account_123 |
    [Arguments]    ${account_id}
    ${response}    Get On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    api/1/rest/admin/account/${account_id}
    RETURN    ${response}

Create Account Api
    [Documentation]    Creates a new account in the specified path.
    ...
    ...    *Arguments:*
    ...    - ``path``: Path where the account should be created
    ...    - ``account_name``: Name of the account to create
    ...    - ``payload``: JSON payload with account details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Account Api | my_path | my_account | ${payload} |
    [Arguments]    ${path}    ${account_name}    ${payload}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    api/1/rest/admin/account/${path}/${account_name}
    ...    json=${payload}
    Log    Create Accounts API URL is...${response.url}    level=CONSOLE
    RETURN    ${response}

Upload File Api
    [Documentation]    Uploads a file to a specified path.
    ...
    ...    *Arguments:*
    ...    - ``sl_path``: Path where the file should be uploaded
    ...    - ``fileName``: Name to use for the uploaded file
    ...    - ``file_path``: Local path to the file to upload
    ...
    ...    *Example:*
    ...    | Upload File Api | my_path | file.txt | /local/path/to/file.txt |
    [Arguments]    ${sl_path}    ${fileName}    ${file_path}
    Log To Console    uploading ${file_path} to ${sl_path}
    ${file_open_path}    Get File For Streaming Upload    ${file_path}
    ${files}    Create Dictionary    file    ${file_open_path}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/slfs/${sl_path}/${fileName}
    ...    files=${files}

Get Asset Details Api
    [Documentation]    Retrieves details about a specific asset.
    ...
    ...    *Arguments:*
    ...    - ``asset_name``: Name of the asset
    ...    - ``path``: Path to the asset
    ...    - ``asset_type``: Type of the asset
    ...    - ``exact_search``: Whether to use exact matching (default: False)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Asset Details Api | my_asset | my_path | Directory | ${TRUE} |
    [Arguments]    ${asset_name}    ${path}    ${asset_type}    ${exact_search}=False
    ${params}    Create Dictionary    exact_search=${exact_search}    asset_type=${asset_type}
    ${response}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/asset/${path}/${asset_name}
    ...    params=${params}
    Log To Console    Get Asset Details API URL is...${response.url}
    RETURN    ${response}

Get Account Id By Name And Path
    [Documentation]    Retrieves account ID by account name and path.
    ...
    ...    *Arguments:*
    ...    - ``account_name``: Name of the account
    ...    - ``path``: Path to the account
    ...
    ...    *Returns:*
    ...    - The account ID
    ...
    ...    *Example:*
    ...    | ${account_id} | Get Account Id By Name And Path | my_account | my_path |
    [Arguments]    ${account_name}    ${path}
    ${params}    Create Dictionary
    ...    exact_search=True
    ...    asset_type=Account
    ...    search=${account_name}
    ${response}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/asset/list/${path}
    ...    params=${params}

    ${asset_id}    Retrieve Asset Id    ${response.json()}
    Log To Console    asset_id::${asset_id}
    ${account}    Get Account Api    ${asset_id}
    RETURN    ${account.json()['response_map']['_id']}

Delete Account Api
    [Documentation]    Deletes a specific account.
    ...
    ...    *Arguments:*
    ...    - ``asset_id``: ID of the account to delete
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete Account Api | account_123 |
    [Arguments]    ${asset_id}
    ${response}    DELETE On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/admin/account/${asset_id}
    Log To Console    Delete Account Api URL is...${response.url}
    RETURN    ${response}

Import Pipeline Api
    [Documentation]    Imports a pipeline to a specified path.
    ...
    ...    *Arguments:*
    ...    - ``path``: Path where the pipeline should be imported
    ...    - ``pipeline_payload``: JSON payload with pipeline details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Import Pipeline Api | my_path | ${payload} |
    [Arguments]    ${path}    ${pipeline_payload}
    Log    Org Snode Id is:${ORG_SNODE_ID}    level=CONSOLE
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/2/${ORG_SNODE_ID}/rest/project/import/pipe/slp/${path}
    ...    params=duplicate_check=false
    ...    json=${pipeline_payload}
    RETURN    ${response}

Export Assets Api
    [Documentation]    Exports assets from a specified path.
    ...
    ...    This keyword exports assets as a ZIP file from the specified project path.
    ...    The export is forced to include all dependencies.
    ...
    ...    *Arguments:*
    ...    - ``project_path``: Full path to the project (e.g., org_name/project_space/project_name)
    ...    - ``asset_types``: Type of asset to export (default: All)
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call containing the exported assets ZIP
    ...
    ...    *Examples:*
    ...    | ${response} = | Export Assets Api | my_org/my_space/my_project |
    ...    |
    ...    | # With custom asset types |
    ...    | ${response} = | Export Assets Api | my_org/my_space/my_project | asset_types=Pipeline |
    ...    |
    ...    | # Save exported file |
    ...    | ${response} = | Export Assets Api | my_org/my_space/my_project |
    ...    | Create Binary File | exported_assets.zip | ${response.content} |
    ...
    ...    *Note:* Requires global variable ``${ORG_SNODE_ID}`` to be set with the organization snode ID
    ...
    ...    *See also:* `Import Pipeline Api`
    [Arguments]    ${project_path}    ${asset_types}=All    ${expected_status}=200
    # Create query parameters with force always set to True
    ${params}    Create Dictionary    force=True    asset_types=${asset_types}
    # Make the API call
    ${response}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/2/${ORG_SNODE_ID}/rest/project/export/${project_path}
    ...    params=${params}
    ...    expected_status=${expected_status}
    Log    Export Assets API URL is: ${response.url}    level=CONSOLE
    Log    Export Assets Response Status: ${response.status_code}    level=CONSOLE
    RETURN    ${response}

Import Assets From Zip Api
    [Documentation]    Imports assets from an exported ZIP file to a specified path.
    ...
    ...    This keyword imports assets (pipelines, accounts, etc.) from a previously exported
    ...    ZIP file. The ZIP file should be in the format created by Export Assets Api.
    ...    By default, duplicate checking is disabled to allow re-imports.
    ...
    ...    *Arguments:*
    ...    - ``import_path``: Target path where assets should be imported (e.g., org_name/project_space/project_name)
    ...    - ``zip_file_path``: Local path to the exported ZIP file to import
    ...    - ``duplicate_check``: Whether to check for duplicates (default: false)
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call containing import results
    ...
    ...    *Examples:*
    ...    | # Import from exported ZIP file |
    ...    | ${response} = | Import Assets From Zip Api | my_org/my_space/new_project | ${OUTPUTDIR}/exported_assets.zip |
    ...    |
    ...    | # Import with duplicate checking enabled |
    ...    | ${response} = | Import Assets From Zip Api | my_org/my_space/project | backup.zip | duplicate_check=true |
    ...
    ...    *Note:* Requires global variable ``${ORG_SNODE_ID}`` to be set with the organization snode ID
    ...
    ...    *See also:* `Export Assets Api`, `Import Pipeline Api`
    [Arguments]
    ...    ${import_path}
    ...    ${zip_file_path}
    ...    ${duplicate_check}=false
    ...    ${expected_status}=200

    Log    📦 Preparing to import ZIP file from: ${zip_file_path}    level=CONSOLE

    # Read the ZIP file for streaming upload (does not unzip)
    ${file_data}    Get File For Streaming Upload    ${zip_file_path}

    # Prepare the files dictionary for multipart upload
    ${files}    Create Dictionary    file=${file_data}

    # Create query parameters
    ${params}    Create Dictionary    duplicate_check=${duplicate_check}

    # Make the API call
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/2/${ORG_SNODE_ID}/rest/project/import/${import_path}
    ...    files=${files}
    ...    params=${params}
    ...    expected_status=${expected_status}

    Log    Import Assets API URL is: ${response.url}    level=CONSOLE
    Log    Import Assets Response Status: ${response.status_code}    level=CONSOLE
    Log    Import Result: ${response.json()}    level=CONSOLE

    RETURN    ${response}

Create Task Api
    [Documentation]    Creates a new task.
    ...
    ...    *Arguments:*
    ...    - ``task_payload``: JSON payload with task details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Task Api | ${payload} |
    [Arguments]    ${task_payload}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/slsched/job
    ...    params=duplicate_check=True
    ...    json=${task_payload}
    Log To Console    Create Task Api URL is:${response.url}
    RETURN    ${response}

Run Triggered Task Api
    [Documentation]    Runs a triggered task with specified parameters.
    ...
    ...    *Arguments:*
    ...    - ``path``: Path to the task
    ...    - ``task_name``: Name of the task to run
    ...    - ``params``: Parameters for running the task
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Example:*
    ...    | ${run_params} | Create Dictionary | param1=value1 |
    ...    | Run Triggered Task Api | my_path | my_task | ${run_params} | 200 |
    [Arguments]    ${path}    ${task_name}    ${params}    ${expected_status}=200

    TRY
        ${response}    Get On Session
        ...    ${ORG_ADMIN_SESSION}
        ...    /api/1/rest/slsched/feed/${path}/${task_name}
        ...    params=${params}
        ...    expected_status=any

        Log    Run Task Api URL is:${response.url}

        # Handle the API error with our common function
        ${response}    Handle API Error    ${response}    task [${task_name}]    running

        # Additional check for successful status code
        IF    ${response.status_code} != ${expected_status}
            Fail    Expected status code ${expected_status} but got ${response.status_code}
        END

        Log    Execute triggered task response is:${response}
        RETURN    ${response}
    EXCEPT    AS    ${error}
        Handle API Error    ${error}    task [${task_name}]    run    is_exception=True
    END

Execute Pipeline Api
    [Documentation]    Executes a pipeline with specified parameters.
    ...
    ...    *Arguments:*
    ...    - ``pipeline_snode_ID``: The snode ID of the pipeline to execute
    ...    - ``run_pipeline_payload``: JSON payload with execution parameters
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Execute Pipeline Api | pipeline_123 | ${payload} | 200 |
    [Arguments]    ${pipeline_snode_ID}    ${run_pipeline_payload}    ${expected_status}=200
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/pipeline/prepare/${pipeline_snode_ID}
    ...    json=${run_pipeline_payload}
    ...    expected_status=${expected_status}
    Log To Console    Execute pipeline response code is :${response.status_code}
    Log To Console    Response URL for_Execute Pipeline Api_ is...${response.url}
    RETURN    ${response}

Get Run Time Pipeline Api
    [Documentation]    Retrieves runtime information for a specific pipeline execution.
    ...
    ...    *Arguments:*
    ...    - ``pipeline_ruuid``: Runtime UUID of the pipeline execution
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Run Time Pipeline Api | runtime_uuid_123 | 200 |
    [Arguments]    ${pipeline_ruuid}    ${expected_status}=200
    ${params}    Create Dictionary    level=detail
    ${response}    Get On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/2/${org_snode_id}/rest/pm/runtime/${pipeline_ruuid}
    ...    params=${params}
    ...    expected_status=${expected_status}
    Log To Console    Run Time response code is :${response.status_code}
    Log To Console    Get Run Time Pipeline Api URL is:${response.url}
    RETURN    ${response}

Get Pipeline Logs Api
    [Documentation]    Retrieves logs for a specific pipeline execution.
    ...
    ...    *Arguments:*
    ...    - ``pipeline_ruuid``: Runtime UUID of the pipeline execution
    ...
    ...    *Returns:*
    ...    - Response object from the API call containing pipeline logs
    ...
    ...    *Example:*
    ...    | ${response} = | Get Pipeline Logs Api | runtime_uuid_123 |
    [Arguments]    ${pipeline_ruuid}
    ${params}    Create Dictionary    ruuid=${pipeline_ruuid}
    ${response}    Get On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/public/log/${org_snode_id}
    ...    params=${params}
    RETURN    ${response}

Delete Pipeline Api
    [Documentation]    Deletes a specific pipeline.
    ...
    ...    *Arguments:*
    ...    - ``pipeline_snode_id``: The snode ID of the pipeline to delete
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete Pipeline Api | pipeline_123 |
    [Arguments]    ${pipeline_snode_id}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/pipeline/delete/${pipeline_snode_id}
    Log To Console    Response URL for_Delete PipelineApi_ is...${response.url}
    RETURN    ${response}

Delete Task Api
    [Documentation]    Deletes a specific task.
    ...
    ...    *Arguments:*
    ...    - ``task_snode_id``: The snode ID of the task to delete
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete Task Api | task_123 |
    [Arguments]    ${task_snode_id}
    ${response}    DELETE On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/slsched/job/${task_snode_id}
    RETURN    ${response}

Create Org Api
    [Documentation]    Creates a new organization.
    ...
    ...    *Arguments:*
    ...    - ``PAYLOAD``: JSON payload with organization details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Create Org Api | ${payload} |
    [Arguments]    ${PAYLOAD}
    ${headers}    Create Dictionary    Content-Type=application/json
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    ${url}/api/1/rest/admin/org/provision
    ...    json=${PAYLOAD}
    ...    headers=${headers}
    Log To Console    Response:${response.content}
    RETURN    ${response}

Get Org Snode Id Api
    [Documentation]    Retrieves the snode ID for a specific organization.
    ...
    ...    *Arguments:*
    ...    - ``ORG_NAME``: Name of the organization
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Org Snode Id Api | my_organization |
    [Arguments]    ${ORG_NAME}
    ${GET_SNODE_API_URL}    Set Variable
    ...    ${url}/api/1/rest/slserver/snaplex_cc_details_with_info?subscriber_id=${ORG_NAME}
    ${response}    GET On Session    ${ORG_ADMIN_SESSION}    ${GET_SNODE_API_URL}
    RETURN    ${response}

Set JCC Node Api
    [Documentation]    Sets JCC node parameters.
    ...
    ...    *Arguments:*
    ...    - ``snode_id``: The snode ID of the node
    ...    - ``jcc_payload``: JSON payload with node parameters
    ...    - ``headers``: HTTP headers for the request
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${headers} | Create Dictionary | Content-Type=application/json |
    ...    | ${response} | Set JCC Node Api | node_123 | ${payload} | ${headers} |
    [Arguments]    ${snode_id}    ${jcc_payload}    ${headers}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    ${url}/api/1/rest/plex/nodes/${snode_id}
    ...    json=${jcc_payload}
    ...    headers=${headers}
    RETURN    ${response}

Get Auth Token
    [Documentation]    Gets authentication token via API.
    ...
    ...    *Arguments:*
    ...    - ``username``: Username for authentication
    ...    - ``password``: Password for authentication
    ...
    ...    *Returns:*
    ...    - Authentication token
    ...
    ...    *Example:*
    ...    | ${token} | Get Auth Token | user | pass |
    [Arguments]    ${username}    ${password}

    # Create session if it doesn't exist
    # Create Admin Session

    # Encode credentials
    ${auth_string}    Evaluate    "${username}:${password}"
    ${encoded_str}    Evaluate
    ...    base64.b64encode($auth_string.encode()).decode()
    ...    modules=base64

    # Prepare session URL and headers
    ${session_url}    Set Variable    /api/1/rest/asset/session?caller=${username}
    ${headers}    Create Dictionary    Authorization=Basic ${encoded_str}

    ${resp}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    ${session_url}
    ...    headers=${headers}
    ...    expected_status=200

    # Extract the token from the nested response structure
    ${response}    Set Variable    ${resp.json()}
    ${token}    Get From Dictionary    ${response}[response_map]    token
    Log    Extracted Token: ${token}

    RETURN    ${token}

Extract Cookies From API Response
    [Documentation]    Extracts cookies from an API response.
    ...
    ...    *Arguments:*
    ...    - ``response``: Response object from which to extract cookies
    ...
    ...    *Returns:*
    ...    - Dictionary containing cookies
    ...
    ...    *Example:*
    ...    | ${cookies} | Extract Cookies From API Response | ${response} |
    [Arguments]    ${response}
    ${cookies}    Create Dictionary
    FOR    ${cookie}    IN    @{response.cookies}
        ${name}    Get From Dictionary    ${cookie}    name
        ${value}    Get From Dictionary    ${cookie}    value
        Set To Dictionary    ${cookies}    ${name}    ${value}
    END
    RETURN    ${cookies}

Create Snaplex Api
    [Documentation]    Creates a new Snaplex instance via API.
    ...
    ...    *Arguments:*
    ...    - ``snaplex_payload``: JSON payload with Snaplex configuration details
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | name=my_snaplex | type=GROUND |
    ...    | ${response} | Create Snaplex Api | ${payload} |
    [Arguments]    ${snaplex_payload}
    Log    Snaplex Payload: ${snaplex_payload}
    ${response}    POST On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/plex
    ...    json=${snaplex_payload}
    RETURN    ${response}

Get Snaplex Status Api
    [Documentation]    Retrieves status information for a specified Snaplex instance.
    ...
    ...    *Arguments:*
    ...    - ``plex_path``: Path to the Snaplex instance
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Get Snaplex Status Api | my_plex_path | 200 |
    [Arguments]    ${plex_path}    ${expected_status}=200
    ${params}    Create Dictionary    plex_path=${plex_path}
    ${response}    GET On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/public/snaplex/${org_name}
    ...    params=${params}
    ...    expected_status=${expected_status}
    Log    \nsnapplex status URL is:${response.url}\n    level=CONSOLE
    RETURN    ${response}

Download file Api
    [Documentation]    Downloads the slpropz configuration file for a Snaplex instance.
    ...
    ...    *Arguments:*
    ...    - ``snaplex_payload``: Snaplex configuration information
    ...    - ``project_location``: Location of the project
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call containing the configuration file
    ...
    ...    *Example:*
    ...    | ${payload} | Create Dictionary | key=value |
    ...    | ${response} | Download slpropz file Api | ${payload} | my_project_location | 200 |
    [Arguments]    ${project_location}    ${expected_status}=200
    ${response}    Get On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/plex/config/${org_name}/${project_location}/${groundplex_name}
    ...    expected_status=${expected_status}
    Log    Download slpropz file Api URL is:${response.url}    level=CONSOLE
    RETURN    ${response}

Delete Snaplex Api
    [Documentation]    Deletes a Snaplex instance from the system.
    ...
    ...    *Arguments:*
    ...    - ``snaplex_snode_id``: The snode ID of the Snaplex to delete
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - Response object from the API call
    ...
    ...    *Example:*
    ...    | ${response} | Delete Snaplex Api | snaplex_123 | 200 |
    [Arguments]    ${snaplex_snode_id}    ${expected_status}=200
    ${response}    DELETE On Session
    ...    ${ORG_ADMIN_SESSION}
    ...    /api/1/rest/slsched/job/${snaplex_snode_id}
    RETURN    ${response}

Handle API Error
    [Documentation]    Handles both HTTP errors and exceptions in API operations
    ...    This function handles both response errors and exceptions
    ...    including nested error structures
    ...
    ...    *Arguments:*
    ...    - ``input``: Either a response object or an exception
    ...    - ``resource_name``: Name of the resource being operated on
    ...    - ``operation``: Type of operation being performed (e.g., "creating", "deleting")
    ...    - ``is_exception``: Boolean flag to indicate if input is an exception (default: False)
    ...
    ...    *Returns:*
    ...    - If no error is found and input is a response, returns the response
    ...    - If an error is found, logs it and fails the test
    [Arguments]    ${input}    ${resource_name}    ${operation}    ${is_exception}=${False}

    # Handle exceptions directly if is_exception flag is True
    IF    ${is_exception}
        Log    Exception during ${operation} operation: ${input}    level=ERROR
        Fail    Failed to ${operation} ${resource_name}: ${input}
        # Handle HTTP error responses for non-200 status codes
    ELSE IF    ${input.status_code} >= 400
        ${status_code}    Set Variable    ${input.status_code}

        # Try to parse response content as JSON
        TRY
            ${json}    Evaluate    json.loads('''${input.content}''')    json

            # Extract and log the full error response
            Log    Error ${operation} ${resource_name} (${status_code}): ${json}    level=ERROR

            # Try to extract error message from nested structure
            ${error_msg}    Set Variable    HTTP ${status_code}: Unknown error

            # Check if we have error_list structure using Evaluate
            ${has_error_list}    Evaluate
            ...    'response_map' in $json and 'error_list' in $json['response_map'] and len($json['response_map']['error_list']) > 0

            IF    ${has_error_list}
                ${error_msg}    Set Variable    ${json['response_map']['error_list'][0]['message']}
                Log To Console    ERROR: ${error_msg}
            END

            # Fail with a clean, single error message
            Fail    Failed to ${operation} ${resource_name}: ${error_msg}
        EXCEPT    AS    ${json_error}
            # This should not happen with your API but included for completeness
            Log    Error parsing response content: ${json_error}    level=ERROR
            Fail    Failed to ${operation} ${resource_name}: HTTP ${status_code} error
        END
    END

    # Return the input for successful responses
    RETURN    ${input}
