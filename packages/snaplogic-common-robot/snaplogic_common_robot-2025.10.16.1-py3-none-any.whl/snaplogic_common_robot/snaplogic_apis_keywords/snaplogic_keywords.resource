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
Resource            snaplogic_apis.resource
Resource            common_utilities.resource
Resource            jms.resource


*** Variables ***
${ORG_SNODE_ID}                     ${EMPTY}
${ACCOUNTS_DETAIL}                  ${NONE}
${GLOBAL_SHARED}                    shared
${project_space_setup}              ${FALSE}    # Default value for project space setup
${TRIGGERED_TASK_PAYLOAD_FILE}      ${CURDIR}/../test_data/triggered_task.json
${SNAPLEX_FILE_PATH}                ${CURDIR}/../test_data/slim_groundplex.json


*** Keywords ***
Set Up Data
    [Documentation]    Sets up the SnapLogic testing environment by performing authentication and optional project space provisioning.
    ...
    ...    This keyword is typically used in the initialization phase of API test suites. It performs:
    ...    - Authentication using `Login Api` with the provided credentials
    ...    - Retrieval and global registration of the organization snode ID
    ...    - Conditional deletion and recreation of the project space and project
    ...
    ...    The behavior depends on the global variable `${project_space_setup}`:
    ...    - If set to `'True'`: Deletes the existing project space (if any), and creates a new project space and project
    ...    - If set to `${FALSE}` (default): Skips project space/project creation (assumes they already exist)
    ...
    ...    If `${org_name}` is `${NONE}`, only authentication is performed and the setup exits early.
    ...    The optional `env_file_path` is accepted for interface consistency but is not used within this keyword.
    ...
    ...    *Argument Details:*
    ...    - ``url``: SnapLogic API base URL (e.g., `https://elastic.snaplogic.com`)
    ...    - ``username``: SnapLogic API username (typically org admin)
    ...    - ``password``: Corresponding password
    ...    - ``org_name``: Organization name (used to retrieve snode ID and manage projects)
    ...    - ``project_space``: Project space name to delete/create (conditionally)
    ...    - ``project_name``: Project name to create inside the space
    ...    - ``env_file_path`` (optional): Placeholder for path to an env file (currently unused)
    ...
    ...    *Returns:*
    ...    - The organization’s snode ID (string), or `${NONE}` if `org_name` is `${NONE}`
    ...
    ...    *Global Variables Set:*
    ...    - `${ORG_SNODE_ID}`: Set via `Set Global Variable`
    ...    - `ORG_SNODE_ID`: Also exported as an environment variable
    ...
    ...    *Relies On:*
    ...    - Global variable `${project_space_setup}` (must be defined before calling this keyword)
    ...
    ...    *Examples:*
    ...
    ...    Basic setup as used in test suites |
    ...    | ${org_id} = | Set Up Data | ${URL} | ${ORG_ADMIN_USER} | ${ORG_ADMIN_PASSWORD} | ${ORG_NAME} | ${PROJECT_SPACE} | ${PROJECT_NAME} | ${ENV_FILE_PATH} |
    ...    |
    ...
    ...    Setup with minimal required parameters |
    ...    | ${org_id} = | Set Up Data | https://api.snaplogic.com | User | Password | MyOrg | ProjectSpace | Project |
    ...    |
    ...
    ...    Setup without environment file |
    ...    | ${org_id} = | Set Up Data | https://api.snaplogic.com | User | Password | MyOrg | ProjectSpace | TestProject | ${None} |
    ...    |
    ...
    ...    Skip organization and project setup (only authenticate) |
    ...    | Set Up Data | https://api.snaplogic.com | myuser | mypass | ${NONE} | TestSpace | TestProject |
    ...    |
    ...
    ...    Setup when project_space_setup is disabled (expects existing project space/project) |
    ...    | Set Variable | ${project_space_setup} | False |
    ...    | ${org_id} = | Set Up Data | https://api.snaplogic.com | myuser | mypass | MyOrg | TestSpace | TestProject |
    ...
    ...    Setup with project creation enabled |
    ...    | Set Variable | ${project_space_setup} | True |
    ...    | ${org_id} = | Set Up Data | https://api.snaplogic.com | myuser | mypass | MyOrg | NewSpace | NewProject |
    ...
    ...    *Prerequisites:*
    ...    - Valid SnapLogic API credentials
    ...    - Network connectivity to the SnapLogic platform
    ...    - Proper permissions for organization and project operations
    ...
    ...    *See also:* `Login Api`, `Get Org Snode ID`, `Delete ProjectSpace`, `Create Project Space`, `Create Project`
    [Arguments]
    ...    ${url}
    ...    ${username}
    ...    ${password}
    ...    ${org_name}
    ...    ${project_space}
    ...    ${project_name}
    ...    ${env_file_path}=${None}
    ${auth}    Create List    ${username}    ${password}
    Login Api    ${auth}
    IF    $org_name == $NONE    RETURN
    ${org_snode_id}    Get Org Snode ID    ${org_name}
    Set Global Variable    ${ORG_SNODE_ID}    ${org_snode_id}
    Set Environment Variable    ORG_SNODE_ID    ${org_snode_id}
    Log    Project space is: ${project_space}    level=CONSOLE
    IF    '${project_space_setup}' == 'True'
        Delete ProjectSpace    ${org_name}    ${project_space}
    END
    IF    '${project_space_setup}'=='True'
        Create Project Space    ${org_name}    ${project_space}
    END
    IF    '${project_space_setup}'=='True'
        Create Project    ${org_name}    ${project_space}    ${project_name}
    END
    RETURN    ${org_snode_id}

Get Project List
    [Documentation]    Retrieves the list of projects in a project space.
    ...
    ...    This keyword calls the SnapLogic API to get all projects within a specified
    ...    project space and returns the entries for further processing. It's commonly
    ...    used to check if projects exist before creating new ones or to list all
    ...    available projects in a space.
    ...
    ...    *Argument Details:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space to query
    ...
    ...    *Returns:*
    ...    A list of project entry dictionaries, each containing project metadata such as
    ...    name, asset_type, creation date, and other project properties
    ...
    ...    *Examples:*
    ...    | ${projects} = | Get Project List | my_organization | my_project_space |
    [Arguments]    ${org_name}    ${project_space}

    Log    Project Space [${project_space}] is used"    level=CONSOLE
    ${resp}    Get Project List Api    ${org_name}    ${project_space}
    RETURN    ${resp.json()['response_map']['entries']}

Create Project
    [Documentation]    Creates a new project if it doesn't already exist.
    ...
    ...    This keyword first checks if a project with the specified name already exists
    ...    in the project space. If the project exists, it logs a message and skips creation.
    ...    If the project doesn't exist, it creates a new directory-type project with the
    ...    specified name and default metadata settings.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space where the project will be created
    ...    - ``project_name``: Name of the project to create
    ...
    ...    *Returns:*
    ...    None (logs creation status to console)
    ...
    ...    *Examples:*
    ...    | Create Project | organization | project_space | project |
    [Arguments]    ${org_name}    ${project_space}    ${project_name}

    @{objects}    Get Project List    ${org_name}    ${project_space}
    ${exists}    Evaluate    any('${project_name}' == obj["name"] for obj in $objects)
    IF    ${exists}
        Log    Project Name [${project_name}] exists"    level=CONSOLE
    ELSE
        ${metadata}    Create Dictionary    pattern=false    validation=null
        ${request_payload}    Create Dictionary
        ...    asset_type=Dir
        ...    metadata=${metadata}
        ...    name=${project_name}
        ${resp}    Create Project Api
        ...    ${org_name}
        ...    ${project_space}
        ...    ${project_name}
        ...    ${request_payload}
    END

Get Org List
    [Documentation]    Retrieves the list of assets in an organization.
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    *Returns:*
    ...    - List of organization entries
    ...    *Example:*
    ...    | ${org_entries} | Get Org List | my_organization |
    [Arguments]    ${org_name}
    ${resp}    Get Org List Api    ${org_name}
    RETURN    ${resp.json()['response_map']['entries']}

Create Project Space
    [Documentation]    Creates a new project space if it doesn't already exist.
    ...
    ...    This keyword checks if a project space with the specified name already exists
    ...    in the organization. If it exists, it logs a message and skips creation.
    ...    If it doesn't exist, it creates a new directory-type project space with the
    ...    specified name. Project spaces are containers for organizing multiple projects
    ...    within an organization.
    ...
    ...    *Arguments:*
    ...    - ``org_name``: Name of the organization
    ...    - ``project_space``: Name of the project space to create
    ...
    ...    *Returns:*
    ...    None (logs creation status to console)
    ...
    ...    *Examples:*
    ...
    ...    | Create Project Space | org_name | project_space |
    [Arguments]    ${org_name}    ${project_space}

    @{objects}    Get Org List    ${org_name}
    ${exists}    Evaluate    any('${project_space}' == obj["name"] for obj in $objects)
    IF    ${exists}
        Log    Project Space [${project_space}] exists"    level=CONSOLE
    ELSE
        ${request_payload}    Create Dictionary    asset_type=Dir    name=${project_space}
        Log    Project Space [${project_space}] before creating"    level=CONSOLE
        ${resp}    Create Project Space Api
        ...    ${org_name}
        ...    ${project_space}
        ...    ${request_payload}
        Log    Project Space [${project_space}] created"    level=CONSOLE
    END

Delete ProjectSpace
    [Documentation]    Deletes a SnapLogic project space if it exists in the given organization.
    ...
    ...    This keyword first retrieves the list of all assets in the specified organization
    ...    and checks whether the given project space exists. If found, it calls the deletion API
    ...    to remove the project space and logs the result. If the project space is not found,
    ...    it logs a message and skips the deletion.
    ...
    ...    This is useful in setup or cleanup workflows where you need to ensure a clean
    ...    environment before creating new project spaces.
    ...
    ...    *Argument Details:*
    ...    - ``org_name``: Name of the SnapLogic organization where the project space resides
    ...    - ``project_space``: Name of the project space to delete
    ...
    ...    *Behavior:*
    ...    - Skips deletion if the project space does not exist
    ...    - Logs success or skip reason to the console
    ...
    ...    *Returns:*
    ...    - None
    ...
    ...    *Example:*
    ...    | Delete ProjectSpace | my_organization | my_project_space |
    [Arguments]    ${org_name}    ${project_space}
    @{org_list}    Get Org List    ${org_name}
    ${org_list_exists}    Evaluate    any('${project_space}' == obj["name"] for obj in $org_list)
    IF    ${org_list_exists}
        ${resp}    Delete ProjectSpace Api    ${org_name}    ${project_space}
        Log    ProjectSpace Name [${project_space}] was deleted"    level=CONSOLE
    ELSE
        Log    ProjectSpace Name [${project_space}] do not exist"    level=CONSOLE
    END

Get Org Snode ID
    [Documentation]    Retrieves the snode ID for an organization.
    ...
    ...    *Argument Details:*
    ...    - ``org_name``: Name of the organization
    ...
    ...    *Returns:*
    ...    - The organization's snode ID
    ...
    ...    *Example:*
    ...    | ${snode_id} | Get Org Snode ID | my_organization |
    [Arguments]    ${org_name}
    ${resp}    Get Org List Api    ${org_name}
    RETURN    ${resp.json()['response_map']['entries'][0]['parent_snode_id']}

Create All Accounts
    [Documentation]    Creates all accounts defined in the ${account_payload_path}.
    ...
    ...    This keyword loads environment variables from the specified env file, renders
    ...    account templates with those variables, and creates all defined accounts
    ...    in the SnapLogic platform. It skips creating accounts that already exist
    ...    and updates account class FQIDs to use the latest versions.
    ...
    ...    *Env Variable Dependencies:* [Below variables must be available in env file]
    ...    - ``${acccout_payload_path}``: Path to account template files directory
    ...    - ``${account_location_path}``: Target location path for account creation
    ...    - ``${org_name}``: Organization name (must be set globally)
    ...
    ...    *Arguments Details:*
    ...    - ``env_file_path``: Path to the environment file containing account variable definitions
    ...
    ...    *Returns:*
    ...    None (logs account creation status for each account)
    ...
    ...    *Examples:*
    ...    | Create All Accounts | /path/to/env_file.json |
    [Arguments]    ${env_file_path}

    Log    env_file_path is:${env_file_path}    level=CONSOLE
    ${env_variables}    Load Env Variables    ${env_file_path}
    Log    Accounts_path is:${ACCOUNT_PAYLOAD_PATH}    level=CONSOLE
    ${acc_payloads}    Render Env Variables for JSON File
    ...    ${ACCOUNT_PAYLOAD_PATH}
    ...    ${env_variables}

    # Check if account payloads were found
    IF    $acc_payloads == [] or $acc_payloads == None
        Fail    No account templates found in path: ${ACCOUNT_PAYLOAD_PATH}
    END

    Log    org Name is:${org_name}    level=CONSOLE
    ${entries}    Get Project List    ${org_name}    ${ACCOUNT_LOCATION_PATH}
    ${accounts_entries}    Evaluate    [x for x in $entries if x['asset_type'] == 'Account']
    FOR    ${payload}    IN    @{acc_payloads}
        ${acc_name}    Set Variable    ${payload}[account][property_map][info][label][value]
        ${account_exist}    Evaluate
        ...    any(x for x in $accounts_entries if x['name'] == '${acc_name}')
        IF    ${account_exist}
            Log    Account [${acc_name}] exists, skip creation    level=CONSOLE
        ELSE
            ${class_fqid}    Set Variable    ${payload}[account][class_fqid]
            ${class_fqid}    Get Account Version By Class Fqid    ${class_fqid}
            ${payload}[account][class_fqid]    Set Variable    ${class_fqid}
            Log    Account payoad is: ${payload}    level=CONSOLE
            ${resp}    Create Account API
            ...    ${org_name}/${ACCOUNT_LOCATION_PATH}
            ...    ${acc_name}
            ...    ${payload}
            Log
            ...    Account [${acc_name}] created at location ${org_name}/${ACCOUNT_LOCATION_PATH}
            ...    level=CONSOLE
        END
    END

Create Account
    [Documentation]    Creates an account using a JSON account file with globally loaded environment variables.
    ...
    ...    This keyword loads an account JSON template file and creates the account in SnapLogic.
    ...    It assumes environment variables are already loaded globally (typically in Suite Setup).
    ...    It checks if the account already exists and only creates it if it doesn't.
    ...
    ...    *Argument Details:*
    ...    - ``account_location_path``: Target location path for account creation (e.g., "shared")
    ...    - ``account_file_path``: Path to the account JSON file
    ...    - ``account_name``: Optional custom account name (overrides template name)
    ...
    ...    *Env Variable Dependencies:* [Must be loaded globally before calling this keyword]
    ...    - ``${org_name}``: Organization name (must be set globally)
    ...    - All variables referenced in the account JSON template
    ...
    ...    *Behavior:*
    ...    - Loads account JSON template directly
    ...    - Skips creation if an account with the same name already exists
    ...    - Retrieves the correct version of the account class using `class_fqid`
    ...    - Logs the creation status and important information to the console
    ...
    ...    *Example:*
    ...    | Create Account | ${ACCOUNT_PATH} | /path/to/acc_oracle.json | custom_name |
    ...    | Create Account | ${ACCOUNT_PATH} | /path/to/acc_oracle.json | ${EMPTY} |
    [Arguments]
    ...    ${account_location_path}    # 1st: Location path
    ...    ${account_file_path}    # 2nd: Payload file path
    ...    ${account_name}=${EMPTY}    # 3rd: Custom account name (optional)

    Log    📄 Loading account JSON from: ${account_file_path}    level=CONSOLE

    # Load JSON file directly
    ${env_variables}    Get Environment Variables
    Log    🧩 Rendering account JSON with env variables    level=CONSOLE
    ${payloads}    Render Env Variables for JSON File    ${account_file_path}    ${env_variables}
    ${payload}    Get From List    ${payloads}    0

    # Get the original account name from template
    ${acc_name_from_template}    Set Variable
    ...    ${payload}[account][property_map][info][label][value]

    # Decide which name to use
    IF    '${account_name}' != '${EMPTY}'
        # Custom name provided - use it
        ${acc_name}    Set Variable    ${account_name}
        # Update the payload with custom name
        Set To Dictionary
        ...    ${payload}[account][property_map][info][label]
        ...    value=${account_name}
        Log    ✏️ Using custom account name: ${account_name}    level=CONSOLE
    ELSE
        # No custom name - use template name
        ${acc_name}    Set Variable    ${acc_name_from_template}
        Log    ✏️ Using template account name: ${acc_name}    level=CONSOLE
    END

    Log    🔍 Account Name: ${acc_name}, Org: ${org_name}    level=CONSOLE

    # Check if account already exists
    ${entries}    Get Project List    ${org_name}    ${account_location_path}
    ${accounts_entries}    Evaluate    [x for x in $entries if x['asset_type'] == 'Account']
    ${account_exist}    Evaluate    any(x for x in $accounts_entries if x['name'] == '${acc_name}')

    IF    ${account_exist}
        Log    ✅ Account [${acc_name}] already exists. Skipping creation.    level=CONSOLE
    ELSE
        # Get correct version of account class
        ${class_fqid}    Set Variable    ${payload}[account][class_fqid]
        ${class_fqid}    Get Account Version By Class Fqid    ${class_fqid}
        Set To Dictionary    ${payload}[account]    class_fqid    ${class_fqid}

        Log    🚀 Creating account with payload: ${payload}    level=CONSOLE
        ${resp}    Create Account API
        ...    ${org_name}/${account_location_path}
        ...    ${acc_name}
        ...    ${payload}
        Log
        ...    🎉 Account [${acc_name}] created at ${org_name}/${account_location_path}
        ...    level=CONSOLE
    END

Get Account Version By Class Fqid
    [Documentation]    Resolves the full versioned class FQID for a given base class FQID (typically extracted from an account template).
    ...
    ...    This keyword is useful when account creation requires the latest or correct version of a class FQID.
    ...    It uses cached account metadata (if available) or fetches it fresh via the `GET Accounts Detail` keyword.
    ...    It then extracts the base class identifier from the input `class_fqid`, looks it up in the account details,
    ...    and returns the versioned `class_fqid` that is required to create the account.
    ...
    ...    *Argument Details:*
    ...    - ``class_fqid``: The unversioned or partially versioned class FQID (e.g., `oracle_account_abc123`)
    ...
    ...    *Returns:*
    ...    - The fully qualified and versioned account class FQID (e.g., `oracle_account:abc123:1`)
    ...
    ...    *Behavior:*
    ...    - Uses cached `${ACCOUNTS_DETAIL}` if available
    ...    - If not cached, retrieves account metadata via `GET Accounts Detail`
    ...    - Uses regex to extract class ID before lookup
    ...
    ...    *Example:*
    ...    | ${account_fqid} |    Get Account Version By Class Fqid    |    oracle_account_abc123 |
    ...
    [Arguments]    ${class_fqid}
    IF    ${ACCOUNTS_DETAIL} == None
        ${accounts_detail}    GET Accounts Detail
        ${ACCOUNTS_DETAIL}    Set Variable    ${accounts_detail}
    END

    ${class_fqid_match}    Evaluate    re.search(r"(.+?)_", $class_fqid)
    ${class_id}    Set Variable    ${class_fqid_match.group(1)}
    ${account_detail}    Set Variable    ${ACCOUNTS_DETAIL}[${class_id}]
    ${account_class_fqid}    Set Variable    ${account_detail}[class_fqid]
    RETURN    ${account_class_fqid}

Get Accounts Detail
    [Documentation]    Retrieves detailed metadata for all available account types in the SnapLogic environment.
    ...
    ...    This keyword is typically used to obtain metadata such as class FQIDs, display labels, input schemas,
    ...    and other structural information required to programmatically create or validate accounts.
    ...
    ...    The response is returned as a dictionary containing all available account definitions,
    ...    keyed by class identifiers.
    ...
    ...    *Returns:*
    ...    - A dictionary extracted from the API's `response_map`, containing all account class metadata
    ...
    ...    *Behavior:*
    ...    - Calls the underlying `Get Accounts Detail Api`
    ...    - Parses the response as JSON and extracts the `response_map` field
    ...
    ...    *Example:*
    ...    | ${accounts_detail}=    Get Accounts Detail |

    ${resp}    Get Accounts Detail Api
    RETURN    ${resp.json()['response_map']}

Import Pipeline
    [Documentation]    Imports a pipeline from a JSON file to a specified path.
    ...
    ...    This keyword loads a pipeline definition from a JSON file, wraps it in the
    ...    required import payload structure, sets the pipeline name, and imports it
    ...    to the specified SnapLogic path. The imported pipeline can then be used
    ...    to create triggered tasks or execute directly.
    ...
    ...    *Argument Details:*
    ...    - ``pipeline_file_path``: Path to the pipeline JSON file (.slp file)
    ...    - ``pipeline_name``: Name to assign to the imported pipeline in SnapLogic
    ...    - ``pipeline_path``: Target path where the pipeline will be imported (e.g., /${org}/${project_space}/${project})
    ...
    ...    *Returns:*
    ...    Dictionary containing the response map with information about the imported pipeline,
    ...    including the pipeline's snode_id for future reference
    ...
    ...    *Examples:*
    ...    | ${pipeline_info} = | Import Pipeline | ${PIPELINE_DIR}/my_pipeline.slp | pipeline_name | pipeline_path |
    [Arguments]    ${pipeline_file_path}    ${pipeline_name}    ${path}

    ${pipeline}    Load Json From File    ${pipeline_file_path}
    ${pipeline_new}    Create Dictionary    pipe=EMPTY
    ${pipeline_new}    Set To Dictionary    ${pipeline_new}    pipe=${pipeline}
    ${import_pipeline_payload}    Set Variable    ${pipeline_new}

    # The value of the fields within ${import_pipeline_payload} are modified
    ${import_pipeline_payload}[pipe][property_map][info][label][value]    Set Variable
    ...    ${pipeline_name}
    Log    Payload created for Creating Pipeline is: ${import_pipeline_payload}
    ${response}    Import Pipeline Api    ${org_name}/${path}    ${import_pipeline_payload}
    Log    ...Import Pipeline URL is: ${response.url}    level=CONSOLE
    Log    ...pipeline_name is....:${pipeline_name}    level=CONSOLE
    Log    ...pipeline_filePath is....:${pipeline_file_path}    level=CONSOLE
    Log    ...pipeline:(${pipeline_name})_imported to projectpath...:${path}    level=CONSOLE
    log    ...pipeline_snodeID....:${response.json()['response_map']}
    RETURN    ${response.json()['response_map']}

Export Assets
    [Documentation]    Exports assets from SnapLogic and saves them to a file.
    ...
    ...    This keyword exports assets as a ZIP file from the specified SnapLogic path
    ...    and saves it to the specified local file path. The export includes the asset
    ...    definition and all dependencies.
    ...
    ...    *Argument Details:*
    ...    - ``project_path``: Full path to the project in SnapLogic (e.g., project_space/project_name)
    ...    - ``save_to_file``: Local file path where the exported ZIP will be saved (required)
    ...    - ``asset_types``: Type of asset to export (default: All)
    ...
    ...    *Returns:*
    ...    The HTTP response object containing the exported assets ZIP in response.content
    ...
    ...    *Examples:*
    ...    | # Export and save pipeline
    ...    | ${response} = | Export Assets | my_project_space/my_project | ${OUTPUTDIR}/pipeline_backup.zip |
    ...
    ...    | # Export with custom asset types
    ...    | ${response} = | Export Assets | my_project_space/my_project | ${OUTPUTDIR}/export.zip | asset_types=Account |
    ...
    ...    | # Export with timestamp in filename
    ...    | ${timestamp} = | Get Time | epoch |
    ...    | ${response} = | Export Assets | project_space/project | ${OUTPUTDIR}/assets_${timestamp}.zip |
    ...
    ...    *See also:* `Import Pipeline`, `Export Assets Api`, `Download And Save Binary File`
    [Arguments]    ${project_path}    ${save_to_file}    ${asset_types}=All

    Log    🔽 Exporting assets from: ${org_name}/${project_path}    level=CONSOLE

    # Call the API to export the assets (force is always True internally)
    ${response}    Export Assets Api
    ...    ${org_name}/${project_path}
    ...    asset_types=${asset_types}

    # Check if response is successful
    Should Be Equal As Numbers    ${response.status_code}    200
    ...    msg=Failed to export assets. Status: ${response.status_code}

    Log    ✅ Assets exported successfully    level=CONSOLE

    # Split the full path into directory and filename
    ${save_dir}    ${filename}    Split Path    ${save_to_file}

    # Always save the binary file
    Download And Save Binary File    ${response}    ${save_dir}    ${filename}

    RETURN    ${response}

Import Assets
    [Documentation]    Imports assets from an exported ZIP file into SnapLogic.
    ...
    ...    This keyword imports assets (pipelines, accounts, files, etc.) from a previously
    ...    exported ZIP file into the specified SnapLogic project path. It's the counterpart
    ...    to the Export Assets keyword and allows you to restore or migrate assets between
    ...    environments or projects.
    ...
    ...    *Argument Details:*
    ...    - ``import_path``: Target path where assets should be imported (e.g., project_space/project_name)
    ...    - ``zip_file_path``: Local path to the exported ZIP file to import
    ...    - ``duplicate_check``: Whether to check for duplicates (default: false)
    ...
    ...    *Returns:*
    ...    The HTTP response object containing import results
    ...
    ...    *Examples:*
    ...    | # Import exported assets to a new project
    ...    | ${response} = | Import Assets | new_project_space/new_project | ${OUTPUTDIR}/pipeline_backup.zip |
    ...
    ...    | # Import with duplicate checking enabled
    ...    | ${response} = | Import Assets | project_space/project | backup.zip | duplicate_check=true |
    ...
    ...    | # Import to restore from backup
    ...    | ${response} = | Import Assets | project_space/restored_project | ${CURDIR}/backups/assets_20250115.zip |
    ...
    ...    *Note:*
    ...    - The ZIP file must be in the format created by Export Assets Api
    ...    - By default, duplicate checking is disabled to allow re-imports
    ...    - Assets will be imported with their original names and configurations
    ...
    ...    *See also:* `Export Assets`, `Import Assets From Zip Api`, `Import Pipeline`
    [Arguments]    ${import_path}    ${zip_file_path}    ${duplicate_check}=false

    Log    📦 Importing assets to: ${org_name}/${import_path}    level=CONSOLE
    Log    📂 From ZIP file: ${zip_file_path}    level=CONSOLE

    # Verify ZIP file exists
    File Should Exist    ${zip_file_path}
    ...    msg=Import failed: ZIP file not found at ${zip_file_path}

    # Call the API to import the assets
    ${response}    Import Assets From Zip Api
    ...    ${org_name}/${import_path}
    ...    ${zip_file_path}
    ...    duplicate_check=${duplicate_check}

    # Check if response is successful
    Should Be Equal As Numbers    ${response.status_code}    200
    ...    msg=Failed to import assets. Status: ${response.status_code}

    # Log import summary
    ${import_result}    Set Variable    ${response.json()}
    Log    ✅ Assets imported successfully    level=CONSOLE
    Log    Import Result: ${import_result}    level=CONSOLE

    RETURN    ${response}

Export Assets Template
    [Documentation]    Template keyword for exporting SnapLogic assets to a local backup file.
    ...    This is a wrapper around the Export Assets keyword that can be used with
    ...    Robot Framework's [Template] syntax for data-driven testing.
    ...
    ...    📋 FUNCTIONALITY:
    ...    • Creates the output directory if it doesn't exist
    ...    • Exports assets from the specified SnapLogic project path
    ...    • Saves the exported ZIP file to the local file system
    ...    • Validates the export was successful
    ...
    ...    📋 ARGUMENTS:
    ...    • project_path - Path to the project in SnapLogic (relative to org)
    ...    • save_to_file - Local file path where the ZIP will be saved
    ...    • asset_types - Optional type of assets to export (default: All)
    ...
    ...    📝 USAGE:
    ...    | [Template] | Export Assets Template |
    ...    | shared/pipelines | ${CURDIR}/backup/assets.zip |
    [Arguments]    ${project_path}    ${save_to_file}    ${asset_types}=All

    Log    📦 Exporting assets from project: ${project_path}    console=yes
    Log    💾 Saving to: ${save_to_file}    console=yes

    ${response}    Export Assets
    ...    ${project_path}
    ...    ${save_to_file}
    ...    asset_types=${asset_types}

    Log    ✅ Assets exported successfully!    console=yes
    Log    📁 Backup file: ${save_to_file}    console=yes

Import Assets Template
    [Documentation]    Template keyword for importing SnapLogic assets from a backup ZIP file.
    ...    This is a wrapper around the Import Assets keyword that can be used with
    ...    Robot Framework's [Template] syntax for data-driven testing.
    ...
    ...    📋 FUNCTIONALITY:
    ...    • Verifies the ZIP file exists before attempting import
    ...    • Imports assets from the backup ZIP to the specified SnapLogic project path
    ...    • Validates the import was successful
    ...    • Logs import results and details
    ...
    ...    📋 ARGUMENTS:
    ...    • import_path - Target path in SnapLogic where assets will be imported (relative to org)
    ...    • zip_file_path - Local file path to the backup ZIP file
    ...    • duplicate_check - Optional flag to prevent duplicate imports (default: false)
    ...
    ...    📝 USAGE:
    ...    | [Template] | Import Assets Template |
    ...    | shared/restored_pipelines | ${CURDIR}/backup/assets.zip | false |
    [Arguments]    ${import_path}    ${zip_file_path}    ${duplicate_check}=True

    Log    📦 Importing assets from backup: ${zip_file_path}    console=yes
    Log    🎯 Target location: ${import_path}    console=yes
    Log    🔄 Duplicate check: ${duplicate_check}    console=yes

    ${response}    Import Assets
    ...    ${import_path}
    ...    ${zip_file_path}
    ...    duplicate_check=${duplicate_check}

    Log    ✅ Assets imported successfully!    console=yes
    Log    📊 Import result: ${response.json()}    console=yes

GET Runtime Path Id
    [Documentation]    Retrieves the runtime path ID for a specified organization and plex.
    ...
    ...    *Argument Details:*
    ...    - ``org_name``: Organization name (default: ${org_name})
    ...    - ``default_plex``: Plex name to find (default: ${default_plex})
    ...
    ...    *Returns:*
    ...    - The runtime path ID corresponding to the specified plex
    ...
    ...    *Example:*
    ...    | ${runtime_id} | GET Runtime Path Id | my_org | my_plex |
    [Arguments]    ${org_name}=${org_name}    ${default_plex}=${default_plex}
    ${response}    GET Runtime Path Id Api    ${org_name}
    @{snaplex_list}    Set Variable    ${response.json()['response_map']}
    FOR    ${line}    IN    @{snaplex_list}
        IF    $line['label'] == $default_plex
            RETURN    ${line['runtime_path_id']}
        END
    END

Create Triggered Task
    [Documentation]    Creates a triggered task using the given pipeline and plex configuration.
    ...
    ...    This keyword builds and submits a task definition payload using a predefined JSON template.
    ...    It sets required fields such as the pipeline snode ID and runtime path ID, and conditionally
    ...    adds optional fields like pipeline parameters, execution timeout, notifications, and task behavior.
    ...
    ...    *Argument Details:*
    ...    - ``task_name``: Name of the new task to be created
    ...    - ``pipeline_snodeid``: Unique snode ID of the pipeline to run
    ...    - ``plex_name``: Name of the Snaplex (runtime environment) where the task will execute
    ...    - ``project_path``: Full SnapLogic path (org/project/project_space) where the task should reside
    ...    - ``pipeline_params``: Dictionary of runtime parameters to pass to the pipeline (optional)
    ...    - ``execution_timeout``: Optional timeout in seconds for task execution
    ...    - ``notification``: Optional dictionary with notification settings (e.g., email/slack recipients and states)
    ...    - ``num_instances``: Optional number of parallel task instances
    ...    - ``debug_next_runs``: Optional number of debug runs to schedule
    ...
    ...    *Returns:*
    ...    - A tuple: ``(${task_payload}, ${task_snode_id})`` — where `task_payload` is the final task definition sent
    ...
    ...    *Examples:*
    ...
    ...    Basic usage
    ...    | ${task_payload}    ${task_snode_id} | Create Triggered Task | task_name | pipeline_snodeid | plex_name | project_path |
    ...
    ...    With parameters and timeout
    ...
    ...    ${params}=    Create Dictionary    key1=value1
    ...    | ${task_payload}    ${task_snode_id} | Create Triggered Task | task_name | pipeline_snodeid | plex_name | project_path | pipeline_params=${params} | execution_timeout=120 |
    ...
    ...    Full example with notifications
    ...
    ...    | ${notification}=    Create Dictionary    email=${TRUE}    recipients=dev@example.com |
    ...    | ${task_payload}    ${task_snode_id} | Create Triggered Task | task_name | pipeline_snodeid | plex_name | project_path    | notification=${notification} | num_instances=3 | debug_next_runs=2 |
    ...
    [Arguments]    ${task_name}    ${pipeline_snodeid}    ${plex_name}    ${path}
    ...    ${pipeline_params}=${None}    ${execution_timeout}=${None}    ${notification}=${None}
    ...    ${num_instances}=${None}    ${debug_next_runs}=${None}

    Log    Current directory: ${CURDIR}    level=CONSOLE
    ${payload}    Set Variable    ${TRIGGERED_TASK_PAYLOAD_FILE}
    ${task_payload}    Load Json From File    ${payload}
    Log    payload is: ${payload}    level=CONSOLE
    ${task_payload}    Load Json From File    ${payload}
    ${runtime_path_id}    GET Runtime Path Id    ${org_name}    ${plex_name}
    Log    Plex_name is: ${plex_name}    level=CONSOLE
    Log    runtime_path_id is: ${runtime_path_id}    level=CONSOLE

    # Only update these basic fields
    Set To Dictionary    ${task_payload}    path_id=${org_name}/${path}
    Set To Dictionary    ${task_payload}    job_name=${task_name}
    Set To Dictionary    ${task_payload}    name=${task_name}
    Set To Dictionary    ${task_payload}    org_path=/${org_name}

    ${parameters_value}    Get From Dictionary    ${task_payload}    parameters

    # Always update these required fields
    Set To Dictionary    ${parameters_value}    runtime_path_id=${runtime_path_id}
    Set To Dictionary    ${parameters_value}    pipeline_snode_id=${pipeline_snodeid}

    # Only update pipeline_parameters if provided
    IF    ${pipeline_params} is not ${None}
        IF    'pipeline_parameters' not in $parameters_value
            Set To Dictionary    ${parameters_value}    pipeline_parameters=&{EMPTY}
        END
        Set To Dictionary    ${parameters_value}[pipeline_parameters]    &{pipeline_params}
    END

    # Only update execution_timeout if provided
    IF    ${execution_timeout} is not ${None}
        Set To Dictionary    ${parameters_value}    execution_timeout=${execution_timeout}
    END

    # Only update notification if provided
    IF    ${notification} is not ${None}
        Set To Dictionary    ${parameters_value}    notification=${notification}
    END

    # Only update num_instances if provided
    IF    ${num_instances} is not ${None}
        Set To Dictionary    ${parameters_value}    num_instances=${num_instances}
    END

    # Only update debug_next_runs if provided
    IF    ${debug_next_runs} is not ${None}
        Set To Dictionary    ${parameters_value}    debug_next_runs=${debug_next_runs}
    END

    Log    Payload created for Creating Task: ${task_payload}    level=CONSOLE
    ${response}    Create Task Api    ${task_payload}
    Should Be Equal As Strings    ${response.status_code}    201
    RETURN    ${task_payload}    ${response.json()['response_map']['snode_id']}

Run Triggered Task
    [Documentation]    Executes a SnapLogic triggered task located at the given path, with optional query parameters.
    ...
    ...    This keyword wraps the `Run Triggered Task Api` call with automatic retry logic using
    ...    `Wait Until Keyword Succeeds`. It retries the task execution up to 30 seconds (every 5 seconds)
    ...    in case of transient failures (e.g., network latency or temporary unavailability).
    ...
    ...    Optional parameters can be passed as a URL-style query string (e.g., `param1=value1&param2=value2`).
    ...    This is useful when triggering pipelines that accept runtime parameters via task execution.
    ...
    ...    *Argument Details:*
    ...    - ``path``: Full SnapLogic path to the project where the task resides (e.g., `/org/space/project`)
    ...    - ``task_name``: Name of the triggered task to run
    ...    - ``params`` (optional): Query string with parameters to pass at runtime (e.g., `debug=true&env=dev`)
    ...
    ...    *Returns:*
    ...    - The response object returned from the `Run Triggered Task Api`
    ...
    ...    *Behavior:*
    ...    - Retries the task run for up to 30 seconds (retry interval: 5 seconds)
    ...    - Passes parameters (if provided) to the task at execution time
    ...    - Returns the HTTP response object from the API
    ...    *Example:*
    ...    | ${task_response} | Run Triggered Task | /org/project | My Task | param1=value1&param2=value2 |
    [Arguments]    ${path}    ${task_name}    ${params}=${EMPTY}
    ${response}    Wait Until Keyword Succeeds
    ...    30 sec
    ...    5 sec
    ...    Run Triggered Task Api
    ...    ${path}
    ...    ${task_name}
    ...    ${params}
    RETURN    ${response}

Create Snaplex
    [Documentation]    Creates a new snaplex using configuration from files.
    ...
    ...    *Argument Details:*
    ...    - ``env_file_path``: Path to the environment variables file
    ...    - ``groundplex_name``: Name of the groundplex
    ...    - ``groundplex_env``: Environment of the groundplex
    ...    - ``org_name``: Organization name
    ...    - ``release_build_version``: Release build version Eg: main-30028
    ...    - ``snap_plex_location``: Location where the snaplex will be created
    ...
    ...    *Returns:*
    ...    - A dictionary with the creation status and message
    ...
    ...    *Example:*
    ...    | ${result} | Create Snaplex | env_file_path | groundplex_name | groundplex_env | org_name | release_build_version | snap_plex_location |
    [Arguments]
    ...    ${env_file_path}
    ...    ${GROUNDPLEX_NAME}=${EMPTY}
    ...    ${GROUNDPLEX_ENV}=${EMPTY}
    ...    ${ORG_NAME}=${EMPTY}
    ...    ${RELEASE_BUILD_VERSION}=${EMPTY}
    ...    ${SNAP_PLEX_LOCATION}=${EMPTY}

    Log    snaplex_file_path is: ${snaplex_file_path}    level=CONSOLE
    Log    env_file_path is: ${env_file_path}    level=CONSOLE

    # Log all input parameters to help with debugging
    Log    Input GROUNDPLEX_NAME: ${GROUNDPLEX_NAME}    level=CONSOLE
    Log    Input GROUNDPLEX_ENV: ${GROUNDPLEX_ENV}    level=CONSOLE
    Log    Input ORG_NAME: ${ORG_NAME}    level=CONSOLE
    Log    Input RELEASE_BUILD_VERSION: ${RELEASE_BUILD_VERSION}    level=CONSOLE
    Log    Input SNAP_PLEX_LOCATION: ${SNAP_PLEX_LOCATION}    level=CONSOLE

    # Load environment variables
    ${env_variables}    Load Env Variables    ${env_file_path}

    # Set a default SNAP_PLEX_LOCATION if not in env variables
    ${has_container_path}    Run Keyword And Return Status
    ...    Dictionary Should Contain Key
    ...    ${env_variables}
    ...    SNAP_PLEX_LOCATION
    IF    not ${has_container_path}
        ${org_name}    Get From Dictionary    ${env_variables}    ORG_NAME
        Set To Dictionary    ${env_variables}    SNAP_PLEX_LOCATION=/${org_name}/shared
        Log    Setting default SNAP_PLEX_LOCATION to "/${org_name}/shared"    level=CONSOLE
    END

    # Store original values for logging
    ${original_groundplex_name}    Get From Dictionary
    ...    ${env_variables}
    ...    GROUNDPLEX_NAME
    ...    default=Not Found
    ${original_groundplex_env}    Get From Dictionary
    ...    ${env_variables}
    ...    GROUNDPLEX_ENV
    ...    default=Not Found
    ${original_org_name}    Get From Dictionary
    ...    ${env_variables}
    ...    ORG_NAME
    ...    default=Not Found
    ${original_release_build}    Get From Dictionary
    ...    ${env_variables}
    ...    RELEASE_BUILD_VERSION
    ...    default=Not Found
    ${original_snap_plex_path}    Get From Dictionary
    ...    ${env_variables}
    ...    SNAP_PLEX_LOCATION
    ...    default=Not Found

    # Override environment variables with provided arguments if not empty or ${None}
    IF    '${GROUNDPLEX_NAME}' != '${EMPTY}' and '${GROUNDPLEX_NAME}' != '${None}'
        Set To Dictionary    ${env_variables}    GROUNDPLEX_NAME=${GROUNDPLEX_NAME}
        Log
        ...    Updated GROUNDPLEX_NAME from "${original_groundplex_name}" to "${GROUNDPLEX_NAME}"
        ...    level=CONSOLE
    END

    IF    '${GROUNDPLEX_ENV}' != '${EMPTY}' and '${GROUNDPLEX_ENV}' != '${None}'
        Set To Dictionary    ${env_variables}    GROUNDPLEX_ENV=${GROUNDPLEX_ENV}
        Log
        ...    Updated GROUNDPLEX_ENV from "${original_groundplex_env}" to "${GROUNDPLEX_ENV}"
        ...    level=CONSOLE
    END

    IF    '${ORG_NAME}' != '${EMPTY}' and '${ORG_NAME}' != '${None}'
        Set To Dictionary    ${env_variables}    ORG_NAME=${ORG_NAME}
        Log    Updated ORG_NAME from "${original_org_name}" to "${ORG_NAME}"    level=CONSOLE
    END

    IF    '${RELEASE_BUILD_VERSION}' != '${EMPTY}' and '${RELEASE_BUILD_VERSION}' != '${None}'
        Set To Dictionary    ${env_variables}    RELEASE_BUILD_VERSION=${RELEASE_BUILD_VERSION}
        Log
        ...    Updated RELEASE_BUILD_VERSION from "${original_release_build}" to "${RELEASE_BUILD_VERSION}"
        ...    level=CONSOLE
    END

    # Update SNAP_PLEX_LOCATION in env variables if provided
    IF    '${SNAP_PLEX_LOCATION}' != '${EMPTY}' and '${SNAP_PLEX_LOCATION}' != '${None}'
        Set To Dictionary
        ...    ${env_variables}
        ...    SNAP_PLEX_LOCATION=/${org_name}/${SNAP_PLEX_LOCATION}/
        Log
        ...    Updated SNAP_PLEX_LOCATION from "${original_snap_plex_path}" to "${SNAP_PLEX_LOCATION}"
        ...    level=CONSOLE
    END

    # Add special mapping for CONTAINER_PATH (for template compatibility)
    ${snap_plex_location}    Get From Dictionary    ${env_variables}    SNAP_PLEX_LOCATION
    Set To Dictionary    ${env_variables}    CONTAINER_PATH=${snap_plex_location}
    Log    Set CONTAINER_PATH to match SNAP_PLEX_LOCATION: ${snap_plex_location}    level=CONSOLE

    ${snaplex_file_path}    Set Variable    ${CURDIR}/../test_data/slim_groundplex.json
    ${snaplex_payloads}    Render Env Variables for JSON File
    ...    ${snaplex_file_path}
    ...    ${env_variables}

    # Assuming your function returns a list, take the first item or iterate as needed
    ${payload}    Set Variable    ${snaplex_payloads}[0]

    # Check if container_path is correctly rendered in the payload
    ${container_path_in_payload}    Get From Dictionary    ${payload}    container_path
    Log    container_path in rendered payload: ${container_path_in_payload}    level=CONSOLE

    # Ensure the container_path in the payload matches our location value
    ${snap_plex_location}    Get From Dictionary    ${env_variables}    SNAP_PLEX_LOCATION
    Set To Dictionary    ${payload}    container_path=${snap_plex_location}
    Log    Ensuring container_path in payload is set to: ${snap_plex_location}    level=CONSOLE

    Log    Final snaplex configuration: ${payload}    level=CONSOLE

    # Now send the fully rendered payload to the API
    # Try to create snaplex
    ${status}    ${response}    Run Keyword And Ignore Error    Create Snaplex Api    ${payload}

    # Success case: 201 Created
    ${is_success}    Run Keyword And Return Status
    ...    Run Keywords
    ...    Should Be Equal    ${status}    PASS    AND
    ...    Should Be Equal As Strings    ${response.status_code}    201

    # Conflict case: 409 Conflict
    ${is_conflict}    Run Keyword And Return Status
    ...    Run Keywords
    ...    Should Be Equal    ${status}    FAIL    AND
    ...    Should Contain    ${response}    409

    # Handle 409 conflict case
    IF    ${is_conflict}
        ${result}    Log
        ...    ***Resource already exists (409 Conflict). Skipping creation****.
        ...    level=CONSOLE
        ${result}    Evaluate    {"status": "success", "message": "Resource already exists"}
    ELSE
        ${result}    Set Variable    ${None}
    END

    # Handle 201 success case
    IF    ${is_success}
        ${result}    Evaluate    {"status": "success", "message": "Resource created"}
    ELSE IF    ${is_conflict}
        ${result}    Set Variable    ${result}
    ELSE
        ${result}    Set Variable    ${None}
    END

    # Fail if neither condition is met
    IF    not ${is_success} and not ${is_conflict}
        Fail    Status is neither 409 nor 201. Error: ${response}
    END
    RETURN    ${result}

Download And Save Config File
    [Documentation]    Downloads a `.slpropz` configuration file from a given URL and saves it to a specified directory.
    ...
    ...    This keyword ensures that the target directory exists, downloads the configuration file from
    ...    the provided project location , and saves it locally with the specified filename .
    ...
    ...    *Argument Details:*
    ...    - ``CONFIG_DIR``: Local directory where the file should be saved (will be created if it doesn't exist)
    ...    - ``PROJECT_LOCATION``: SnapLogic project path or remote source from which the config file is downloaded
    ...    - ``FILE_NAME``: Desired filename to use when saving the file (e.g., `config.slpropz`)
    ...
    ...    *Behavior:*
    ...    - Creates the target directory if it doesn't exist
    ...    - Downloads the file content using the `Download slpropz file Api`
    ...    - Writes the content as a binary file to the target path
    ...    - Logs the saved file path to the console
    ...
    ...    *Returns:*
    ...    - None (logs file creation status)
    ...
    ...    *Example:*
    ...    | Download And Save Config File | CONFIG_DIR | PROJECT_LOCATION | FILE_NAME|
    ...
    [Arguments]    ${CONFIG_DIR}    ${PROJECT_LOCATION}    ${FILE_NAME}
    Create Directory If Not Exists    ${CONFIG_DIR}
    ${response}    Download file Api    ${PROJECT_LOCATION}
    Create Binary File    ${CONFIG_DIR}/${FILE_NAME}    ${response.content}
    Log    File saved to ${CONFIG_DIR}/${FILE_NAME}    level=CONSOLE

Download And Save Binary File
    [Documentation]    Generic keyword to download and save any binary content from an HTTP response.
    ...
    ...    This is a reusable utility keyword that takes an existing HTTP response object and saves
    ...    its binary content to a specified local directory. Unlike `Download And Save Config File`,
    ...    this keyword does NOT make an API call itself - it only handles the file saving operation.
    ...
    ...    This keyword is useful when you already have a response object from any API call
    ...    (e.g., Export Pipeline Api, Download file Api, etc.) and want to save the content.
    ...
    ...    *Argument Details:*
    ...    - ``response``: HTTP response object containing binary content in response.content
    ...    - ``save_dir``: Local directory where the file should be saved (will be created if it doesn't exist)
    ...    - ``filename``: Desired filename to use when saving the file
    ...
    ...    *Behavior:*
    ...    - Creates the target directory if it doesn't exist
    ...    - Extracts binary content from response.content
    ...    - Writes the content as a binary file to the target path
    ...    - Logs the saved file path and file size to the console
    ...
    ...    *Returns:*
    ...    - None (logs file creation status)
    ...
    ...    *Examples:*
    ...    | # Save exported pipeline
    ...    | ${response} = | Export Pipeline Api | project_space/project |
    ...    | Download And Save Binary File | ${response} | ${OUTPUTDIR} | pipeline.zip |
    ...
    ...    | # Save downloaded config file
    ...    | ${response} = | Download file Api | project_location |
    ...    | Download And Save Binary File | ${response} | /tmp/configs | config.slpropz |
    ...
    ...    | # Save any binary content
    ...    | ${response} = | GET On Session | session | /api/download/file |
    ...    | Download And Save Binary File | ${response} | ${TEMPDIR} | downloaded_file.dat |
    ...
    ...    *See also:* `Download And Save Config File`, `Export Pipeline`
    [Arguments]    ${response}    ${save_dir}    ${filename}

    # Create directory if it doesn't exist
    Create Directory If Not Exists    ${save_dir}

    # Save the binary content
    ${full_path}    Set Variable    ${save_dir}/${filename}
    Create Binary File    ${full_path}    ${response.content}

    # Get file size for logging
    ${file_size}    Get Length    ${response.content}
    ${size_kb}    Evaluate    ${file_size} / 1024
    ${size_kb_formatted}    Evaluate    "{:.2f}".format(${size_kb})

    Log    💾 File saved to: ${full_path}    level=CONSOLE
    Log    📏 File size: ${size_kb_formatted} KB    level=CONSOLE

Get Snaplex Status
    [Documentation]    Retrieves and extracts the status of a Snaplex instance.
    ...
    ...    This keyword calls the Get Snaplex Status Api and then processes the response
    ...    to extract just the status field from the response structure.
    ...
    ...    *Argument Details:*
    ...    - ``plex_path``: Path to the Snaplex instance
    ...    - ``expected_status``: Expected HTTP status code (default: 200)
    ...
    ...    *Returns:*
    ...    - String containing the Snaplex status value (e.g., "not_running", "up_and_running")
    ...
    ...    *Example:*
    ...    | ${status} | Get Snaplex Status | my_plex_path | expected_status |
    [Arguments]    ${plex_path}    ${expected_status}=200

    ${response}    Get Snaplex Status Api    ${plex_path}    ${expected_status}
    ${json_body}    Set Variable    ${response.json()}
    ${response_map}    Set Variable    ${json_body['response_map']}
    ${first_key}    Evaluate    list(${response_map}.keys())[0]
    ${cc_info}    Get From Dictionary    ${response_map['${first_key}']}    cc_info
    ${status}    Get From Dictionary    ${cc_info}    status
    Log To Console    \nSnaplex status is: ${status}\n
    RETURN    ${status}

Snaplex Status Should Be Running
    [Documentation]    Verifies that the given Snaplex instance is in a healthy state: either `up_and_running` or `alert`.
    ...
    ...    This keyword is typically used in environment validation steps to ensure that the target Snaplex
    ...    is online and ready to execute triggered or scheduled tasks.
    ...
    ...    It checks the Snaplex status using the `Get Snaplex Status` keyword and asserts that the result
    ...    contains either of the following states:
    ...    - `up_and_running` → Snaplex is operational
    ...    - `alert` → Snaplex is running but has warning-level issues
    ...
    ...    *Argument Details:*
    ...    - ``plex_path``: Full path to the Snaplex instance to validate (e.g., `/org/plex_name`)
    ...
    ...    *Behavior:*
    ...    - Logs the current status to console
    ...    - Fails the test if the Snaplex is neither `up_and_running` nor `alert`
    ...
    ...    *Example:*
    ...    | Snaplex Status Should Be Running | /myorg/myplex |
    [Arguments]    ${plex_path}
    ${status}    Get Snaplex Status    ${plex_path}
    Log    Snaplex current status: ${status}
    Should Contain Any    ${status}    up_and_running    alert

Wait Until Plex Status Is Up
    [Documentation]    Waits until the given Snaplex instance reaches the `up_and_running` or `alert` state.
    ...
    ...    This keyword is useful for scenarios where a Snaplex is restarting, undergoing updates, or
    ...    provisioning, and test execution should wait until the Snaplex is ready to handle tasks.
    ...
    ...    Internally, this uses `Wait Until Keyword Succeeds` with:
    ...    - Timeout: 4 minutes
    ...    - Retry interval: every 10 seconds
    ...    - Keyword used for status check: `Snaplex Status Should Be Running`
    ...
    ...    The keyword also logs the time taken for the Snaplex to become ready.
    ...
    ...    *Arguments:*
    ...    - ``plex_path``: Full path to the Snaplex instance (e.g., `/org/shared/groundplex1`)
    ...
    ...    *Returns:*
    ...    - None (fails if the Snaplex does not reach `up_and_running` or `alert` within timeout)
    ...
    ...    *Example:*
    ...    | Wait Until Plex Status Is Up | /myorg/groundplex01 |
    [Arguments]    ${plex_path}
    # Capture start time for log and computation
    ${start_time_str}    Get Time    format=%Y-%m-%d %H:%M:%S
    ${start_ts}    Get Time    epoch

    Log
    ...    \n⏳ Waiting for Snaplex at path '${plex_path}' to become up and running...\n
    ...    level=CONSOLE
    Log    Start Time: ${start_time_str}    level=CONSOLE

    Wait Until Keyword Succeeds
    ...    4 min
    ...    10 sec
    ...    Snaplex Status Should Be Running
    ...    ${plex_path}

    # Capture end time and calculate duration
    ${end_time_str}    Get Time    format=%Y-%m-%d %H:%M:%S
    ${end_ts}    Get Time    epoch
    ${duration_secs}    Evaluate    int(${end_ts} - ${start_ts})
    ${minutes}    Evaluate    ${duration_secs} // 60
    ${seconds}    Evaluate    ${duration_secs} % 60

    Log    \n✅ Snaplex at path '${plex_path}' is now up and running.\n    level=CONSOLE
    Log    End Time: ${end_time_str}    level=CONSOLE
    Log    ⏱️ Total time taken is: ${minutes} minutes and ${seconds} seconds    level=CONSOLE

Create Account From Template
    [Documentation]    Creates an account from a JSON template file using environment-specific variables.
    ...
    ...    This keyword is a simple wrapper around the `Create Account` keyword. It reads an account
    ...    template file (which may contain Jinja-style placeholders), combines it with environment values
    ...    from the provided file, and proceeds with account creation if it doesn't already exist.
    ...
    ...    *Arguments:*
    ...    - ``payload_file_path_and_name``: Full path to the account JSON template file
    ...
    ...    *Env Variable Dependencies:*
    ...    - ``org_name`` and ``acount_location_path`` must be available in the environment file
    ...
    ...    *Returns:*
    ...    - None. Logs the creation status of the account (created or already exists).
    ...
    ...    *Example:*
    ...    | Create Account From Template | ${payload_file_path}/acc_oracle.json | env_file_path |
    [Arguments]    ${account_location_path}    ${payload_file_path_and_name}    ${account_name}

    ${payload_path}    Set Variable    ${account_payload_path}/${payload_file_path_and_name}
    Create Account
    ...    ${account_location_path}
    ...    ${payload_path}
    ...    ${account_name}

Import Pipelines From Template
    [Documentation]    Imports a SnapLogic pipeline with a unique suffix and registers it using suite-level variables for downstream use.
    ...
    ...    This keyword is commonly used in test templates where pipelines are dynamically imported
    ...    with unique identifiers to prevent name collisions during parallel or repeated test executions.
    ...
    ...    It appends the given `unique_id` to the pipeline name before import, and captures the returned
    ...    `snode_id` in a suite variable. These values can then be referenced in later test steps to
    ...    create triggered tasks or run executions.
    ...
    ...    *Arguments:*
    ...    - ``unique_id``: A suffix identifier to make pipeline names unique (e.g., `oracle_pl`)
    ...    - ``pipeline_file_path``: The full path to the directory containing the `.slp` file
    ...    - ``pipeline_name``: The base logical name of the pipeline (without suffix)
    ...    - ``slp_file_name``: The filename of the SnapLogic pipeline to import (e.g., `ML_Oracle.slp`)
    ...
    ...    *Behavior:*
    ...    - Constructs a unique pipeline name by appending `${unique_id}` to `${pipeline_name}`
    ...    - Imports the pipeline using `Import Pipeline` keyword
    ...    - Stores the resulting `snode_id` as a suite variable using the modified pipeline name
    ...
    ...    *Suite Variables Set:*
    ...    - ``${<pipeline_name_with_suffix>_snode_id}``: Contains the `snode_id` from the import result
    ...    Example:
    ...    | Import Pipelines From Template | ${pipeline_file_path} | ${pipeline_name} | ${slp_file_name}    |
    [Arguments]    ${unique_id}    ${project_path}    ${pipeline_name}    ${slp_file_name}

    ${pipeline_name}    Set Variable    ${pipeline_name}_${unique_id}

    ${pipeline_snode_id}    Import Pipeline
    ...    ${PIPELINE_PAYLOAD_PATH}/${slp_file_name}
    ...    ${pipeline_name}
    ...    ${project_path}

    # Set Suite Variable    ${${pipeline_name}_unique_id}    ${unique_id}
    Set Suite Variable    ${${pipeline_name}_snode_id}    ${pipeline_snode_id}

    Log
    ...    📌 Set suite variable: \${${pipeline_name}_snode_id} = ${pipeline_snode_id}
    ...    level=CONSOLE

Create Triggered Task From Template
    [Documentation]    This keyword is a simple wrapper around the `Create Triggered Task` keyword.
    ...
    ...    It constructs a triggered task name using the given pipeline name, task name prefix,
    ...    and a unique identifier. It then dynamically retrieves the pipeline snode ID using
    ...    suite variables and uses that along with optional parameters to create the task.
    ...
    ...    After successful task creation, this keyword stores the resulting task payload and snode ID
    ...    into suite-level variables so that they can be reused in other steps in the test flow.
    ...
    ...    *Argument Details:*
    ...    - ``unique_id``: Unique identifier used to distinguish the task
    ...    - ``project_path``: Path to the SnapLogic project where the task should be created
    ...    - ``pipeline_name``: Name of the pipeline for which the task is created
    ...    - ``task_name``: Name of the Task
    ...    - ``pipeline_params``: Optional dictionary of pipeline parameters
    ...    - ``notification``: Optional dictionary with notification settings (e.g., email, recipients)
    ...    - ``plex_name``: Name of the Snaplex where the task will run (default: `${groundplex_name}`)
    ...
    ...    *Returns:*
    ...    None. Stores results in suite variables.
    ...
    ...    *Suite Variables Created:*
    ...    - ``${<full_task_name>_payload}``: The task payload returned from the API
    ...    - ``${<full_task_name>_snodeid}``: The task's snode ID
    ...
    ...    *Example:*
    ...    | Create Triggered Task From Template | ${unique_id} | /org/shared/project | ml_oracle | ML_Oracle_Task | ${oracle_pipeline_params} | ${task_notification} | ${custom_plex_name} |
    [Arguments]
    ...    ${unique_id}
    ...    ${project_path}
    ...    ${pipeline_name}
    ...    ${task_name}
    ...    ${plex_name}=${groundplex_name}
    ...    ${pipeline_params}=None
    ...    ${notification}=None

    ${full_task_name}    Set Variable    ${pipeline_name}_${task_name}_${unique_id}
    ${pipeline_snode_id}    Get Variable Value    ${${pipeline_name}_${unique_id}_snode_id}
    ${pipeline_params}    Get Variable Value    ${pipeline_params}

    Log    📌 pipeline_snode_id is : ${pipeline_snode_id}    level=CONSOLE
    Log    📌 FullTaskName is : ${full_task_name}    level=CONSOLE

    # ${states}    Create List    Completed    Failed
    # ${notification}    Create Dictionary    recipients=newemail@gmail.com    states=${states}

    ${task_payload}    ${task_snode_id}    Create Triggered Task
    ...    ${full_task_name}
    ...    ${pipeline_snode_id}
    ...    ${plex_name}
    ...    ${project_path}
    ...    pipeline_params=${pipeline_params}
    ...    notification=${notification}

    Log Pretty JSON    CREATED_TASK    ${task_payload}

    Set Suite Variable    ${${full_task_name}_payload}    ${task_payload}
    Set Suite Variable    ${${full_task_name}_snodeid}    ${task_snode_id}
    Log
    ...    📌 Set suite variable task_payoad_var: ${full_task_name}_payload=${task_payload}
    ...    level=CONSOLE
    Log
    ...    📌 Set suite variable task_snode_id: ${full_task_name}_snodeid=${task_snode_id}
    ...    level=CONSOLE

Run Triggered Task With Parameters From Template
    [Documentation]    Updates the parameters of a previously created triggered task from a template and runs it.
    ...
    ...    This keyword locates a triggered task using a composed name (based on pipeline name, task name,
    ...    and a unique ID), loads its payload from a stored suite variable, merges the given parameter
    ...    overrides into the existing pipeline parameters, updates the task via API, and then executes it.
    ...
    ...    It logs both the original and updated task payloads for traceability and returns the final
    ...    payload along with the execution job ID.
    ...
    ...    *Argument Details:*
    ...    - ``unique_id``: Unique identifier to distinguish the task instance
    ...    - ``project_path``: Full SnapLogic project path where the task resides (e.g., `/org/space/project`)
    ...    - ``pipeline_name``: Name of the pipeline the task is linked to
    ...    - ``task_name``: Name of the task (e.g., `ML_Oracle_Task`)
    ...    - ``new_parameters``: Dictionary of pipeline parameters to override or add
    ...
    ...    *Returns:*
    ...    - A tuple containing:
    ...    - The updated task payload (dictionary)
    ...    - The job ID of the triggered task execution
    ...
    ...    *Behavior:*
    ...    - Retrieves existing task payload and snode ID from suite variables
    ...    - Merges new parameter values into existing `pipeline_parameters`
    ...    - Calls the API to update the task definition
    ...    - Triggers the task and logs job metadata
    ...
    ...    *Examples:*
    ...    | ${new_params}=    Create Dictionary    env=prod    debug=${FALSE} |
    ...    | ${payload}    ${job_id} | Run Triggered Task With Parameters From Template | oracle_pl | project_path | pipeline_name | task_name | new_params |
    [Arguments]
    ...    ${unique_id}
    ...    ${project_path}
    ...    ${pipeline_name}
    ...    ${task_name}
    ...    &{new_parameters}

    ${full_task_name}    Set Variable    ${pipeline_name}_${task_name}_${unique_id}
    ${task_payload}    Get Variable Value    ${${full_task_name}_payload}
    ${task_snode_id}    Get Variable Value    ${${full_task_name}_snodeid}

    # Get the current 'parameters' block from task payload
    ${parameters_value}    Get From Dictionary    ${task_payload}    parameters

    # Extract pipeline_parameters from parameters
    ${existing_pipeline_parameters}    Get From Dictionary
    ...    ${parameters_value}
    ...    pipeline_parameters

    # 📝 Print existing pipeline_parameters before update
    ${existing_json}    Evaluate
    ...    json.dumps($existing_pipeline_parameters, indent=4)
    ...    modules=json
    Log    \n📝 Existing pipeline_parameters BEFORE any update:\n${existing_json}    level=CONSOLE

    # Check if pipeline_parameters is None and create empty dictionary if needed
    ${is_none}    Run Keyword And Return Status
    ...    Should Be Equal
    ...    ${existing_pipeline_parameters}
    ...    ${NONE}
    IF    ${is_none}
        ${existing_pipeline_parameters}    Create Dictionary
    END

    # 🔁 Merge new parameters into existing ones
    FOR    ${key}    ${value}    IN    &{new_parameters}
        Set To Dictionary    ${existing_pipeline_parameters}    ${key}=${value}
    END

    # Set merged parameters back into payload
    Set To Dictionary    ${parameters_value}    pipeline_parameters=${existing_pipeline_parameters}
    Set To Dictionary    ${task_payload}    parameters=${parameters_value}

    # Call API to update the task
    ${response}    Update Task Api    ${task_snode_id}    ${task_payload}

    # ✅ Pretty-print the final task payload
    ${pretty_json}    Evaluate    json.dumps($task_payload, indent=4)    modules=json
    Log    \n==== ✅ UPDATED TASK PAYLOAD ====\n${pretty_json}    level=CONSOLE

    Run Triggered Task    ${org_name}/${project_path}    ${full_task_name}

    RETURN    ${task_payload}    ${response.json()['response_map']['job_id']}

Upload Files
    [Documentation]    Main keyword for uploading single or multiple files to SnapLogic
    ...
    ...    This is the primary upload keyword that handles both individual files and
    ...    batch uploads. It provides comprehensive error handling, file validation,
    ...    and detailed result reporting.
    ...
    ...    *Arguments:*
    ...    - ``files``: Either a single file path (string) or list of file paths
    ...    - ``destination``: SnapLogic destination path where files will be uploaded
    ...    - ``rename_to``: Optional new name for the file (only applies to single file uploads)
    ...
    ...    *Returns:*
    ...    Always returns a list of result dictionaries, even for single file uploads.
    ...    Each dictionary contains:
    ...    - ``file``: Original local file path
    ...    - ``uploaded_as``: Filename used in SnapLogic
    ...    - ``destination``: Upload destination path
    ...    - ``success``: Boolean indicating upload success (True/False)
    ...    - ``message``: Descriptive success or error message
    ...
    ...    *Examples:*
    ...    | # Single file upload
    ...    | @{results} | Upload Files | /tmp/report.csv | project/reports |
    ...    | Should Be True | ${results}[0][success] |
    ...
    ...    | # Single file upload with rename
    ...    | @{results} | Upload Files | /tmp/data.csv | project/archive | data_2025.csv |
    ...
    ...    | # Multiple files upload
    ...    | @{files} | Create List | /tmp/file1.json | /tmp/file2.xml | /tmp/file3.csv |
    ...    | @{results} | Upload Files | ${files} | project/batch |
    ...    | FOR | ${result} | IN | @{results} |
    ...    |    Should Be True | ${result}[success] | ${result}[message] |
    ...    | END |
    ...
    ...    | # Upload with error handling
    ...    | @{results} | Upload Files | /tmp/maybe_missing.txt | project/uploads |
    ...    | IF | not ${results}[0][success] |
    ...    |    Log | Upload failed: ${results}[0][message] | WARN |
    ...    | END |
    ...
    ...    *Error Handling:*
    ...    - File not found: Returns success=False with "File not found" message
    ...    - Upload failure: Returns success=False with error details
    ...    - Never throws exceptions - always returns result dictionary
    ...
    ...    *Performance Notes:*
    ...    - Files are uploaded sequentially, not in parallel
    ...    - Large files may take time - check SnapLogic timeout settings
    ...    - No built-in retry logic - implement at test level if needed
    [Arguments]    ${files}    ${destination}    ${rename_to}=${EMPTY}

    @{upload_list}    Create List

    # Check if input is a single file (string) or list
    ${is_single_file}    Run Keyword And Return Status    Should Be String    ${files}

    IF    ${is_single_file}
        # Single file - add to list
        Append To List    ${upload_list}    ${files}
    ELSE
        # Multiple files - use the list as is
        @{upload_list}    Copy List    ${files}
    END

    # Process all files
    @{results}    Create List
    FOR    ${file_path}    IN    @{upload_list}
        # Handle file naming
        IF    '${rename_to}' != '${EMPTY}' and ${is_single_file}
            ${upload_name}    Set Variable    ${rename_to}
        ELSE
            ${path}    ${upload_name}    Split Path    ${file_path}
        END

        # Check if file exists
        ${file_exists}    Run Keyword And Return Status    File Should Exist    ${file_path}

        IF    not ${file_exists}
            ${status}    Set Variable    ${False}
            ${response}    Set Variable    File not found: ${file_path}
        ELSE
            # Log upload attempt
            Log    Uploading file: ${file_path} to ${destination}/${upload_name}

            # Attempt to upload file
            ${upload_status}    ${response}    Run Keyword And Ignore Error
            ...    Upload File Api    ${destination}    ${upload_name}    ${file_path}

            # Set status and response based on upload result
            IF    '${upload_status}' == 'PASS'
                ${status}    Set Variable    ${True}
                ${response}    Set Variable    Upload successful: ${upload_name}
            ELSE
                ${status}    Set Variable    ${False}
                ${response}    Set Variable    Upload failed: ${response}
            END
        END

        # Create result dictionary
        ${result}    Create Dictionary
        ...    file=${file_path}
        ...    uploaded_as=${upload_name}
        ...    destination=${destination}
        ...    success=${status}
        ...    message=${response}

        Append To List    ${results}    ${result}

        # Log result
        IF    ${status}
            Log    Successfully uploaded ${upload_name}
        ELSE
            Log    Failed to upload ${upload_name}: ${response}    ERROR
        END
    END

    RETURN    @{results}

Upload Files To SnapLogic From Template
    [Documentation]    Template-friendly keyword for data-driven file upload testing
    ...
    ...    Designed for use with Robot Framework's [Template] syntax to define
    ...    multiple upload scenarios in a clean, tabular format. Supports wildcards
    ...    for batch uploads and validates all uploads succeed.
    ...
    ...    *Arguments:*
    ...    - ``source_dir``: Local directory containing files to upload
    ...    - ``file_name``: File name or pattern (supports * and ? wildcards)
    ...    - ``dest_path``: Destination path in SnapLogic
    ...
    ...    *Wildcard Support:*
    ...    - ``*`` matches any number of characters (e.g., *.json matches all JSON files)
    ...    - ``?`` matches single character (e.g., file?.txt matches file1.txt, file2.txt)
    ...
    ...    *Examples:*
    ...    | # Using as template
    ...    | [Template] | Upload Files To SnapLogic From Template |
    ...    | /tmp/data | employees.csv | project/hr/data |
    ...    | /tmp/data | *.json | project/configs |
    ...    | /tmp/logs | app_2025_??.log | project/logs |
    ...
    ...    | # Direct call
    ...    | Upload Files To SnapLogic From Template | /tmp | report.pdf | shared/reports |
    ...
    ...    *Note:* This keyword expects ALL uploads to succeed and will fail the test
    ...    if any file fails to upload
    [Arguments]    ${source_dir}    ${file_name}    ${dest_path}

    # Handle wildcards in file pattern
    IF    '*' in '${file_name}' or '?' in '${file_name}'
        ${files_to_upload}    Find Files With Pattern    ${source_dir}    ${file_name}
    ELSE
        ${files_to_upload}    Create List    ${source_dir}/${file_name}
    END

    # Log upload attempt
    ${file_count}    Get Length    ${files_to_upload}
    Log
    ...    \nUploading ${file_count} file(s) matching: ${file_name} from ${source_dir}
    ...    console=True

    # Upload files - no retry
    @{results}    Upload Files
    ...    ${files_to_upload}
    ...    ${ORG_NAME}/${dest_path}
    ...    ${EMPTY}

    # Verify all uploads succeeded
    ${success_count}    Set Variable    ${0}
    ${fail_count}    Set Variable    ${0}
    @{failed_files}    Create List

    FOR    ${result}    IN    @{results}
        IF    ${result}[success]
            ${success_count}    Evaluate    ${success_count} + 1
            Log    ✓ Successfully uploaded: ${result}[uploaded_as]
        ELSE
            ${fail_count}    Evaluate    ${fail_count} + 1
            Append To List    ${failed_files}    ${result}[file]
            Log    ✗ Failed to upload: ${result}[file] - ${result}[message]    ERROR
        END
    END

    # All uploads should succeed
    Should Be Equal As Numbers
    ...    ${fail_count}
    ...    0
    ...    Failed to upload ${fail_count} file(s): ${failed_files}. Check file paths and permissions.

    Log    \nUpload Summary: All ${success_count} file(s) uploaded successfully!
