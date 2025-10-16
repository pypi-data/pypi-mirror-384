# SnapLogic Common Robot Framework Library

A comprehensive Robot Framework library providing keywords for SnapLogic platform automation and testing.

## 🚀 Features

- **SnapLogic APIs**: Low-level API keywords for direct platform interaction
- **SnapLogic Keywords**: High-level business keywords for common operations  
- **Common Utilities**: Shared utilities for database connections and file operations
- **Comprehensive Documentation**:  After installation, access the comprehensive HTML documentation through index.html

## 📦 Installation

```bash
pip install snaplogic-common-robot
```

## 📋 Usage 

**Important:** This is a Robot Framework resource library containing `.resource` files with Robot Framework keywords, not a Python library. It cannot be imported using Python `import` statements. You must use Robot Framework's `Resource` statement to access the keywords provided by this framework.



### Quick Start Example

```robot
*** Settings ***
Resource          snaplogic_common_robot/snaplogic_apis_keywords/snaplogic_keywords.resource
Resource          snaplogic_common_robot/snaplogic_apis_keywords/common_utilities.resource


*** Test Cases ***
Complete SnapLogic Environment Setup
    [Documentation]    Sets up a complete SnapLogic testing environment
    [Tags]             setup
    
    # Import and Execute Pipeline
    ${pipeline_info}=    Import Pipeline
    ...    ${CURDIR}/pipelines/data_processing.slp
    ...    DataProcessingPipeline
    ...    /${ORG_NAME}/${PROJECT_SPACE}/${PROJECT_NAME}
    

Snaplex Management Example
    [Documentation]    Demonstrates Snaplex creation and monitoring
    [Tags]             snaplex

    # Wait for Snaplex to be ready
    Wait Until Plex Status Is Up    /${ORG_NAME}/shared/${GROUNDPLEX_NAME}
    
    # Verify Snaplex is running
    Snaplex Status Should Be Running    /${ORG_NAME}/shared/${GROUNDPLEX_NAME}
    
    # Download configuration file
    Download And Save Config File
    ...    ${CURDIR}/config
    ...    shared/${GROUNDPLEX_NAME}
    ...    groundplex.slpropz



### Environment Configuration

Create an `env_config.json` file with your environment-specific values:

```json
{
  "ORG_NAME": "your-organization",
  "ORG_ADMIN_USER": "admin@company.com",
  "ORG_ADMIN_PASSWORD": "secure-password",
  "GROUNDPLEX_NAME": "test-groundplex",
  "GROUNDPLEX_ENV": "development",
  "RELEASE_BUILD_VERSION": "main-30028",
  "ACCOUNT_PAYLOAD_PATH": "./test_data/accounts",
  "ACCOUNT_LOCATION_PATH": "shared",
  "ORACLE_HOST": "oracle.example.com",
  "ORACLE_PORT": "1521",
  "ORACLE_SID": "ORCL",
  "ORACLE_USERNAME": "testuser",
  "ORACLE_PASSWORD": "testpass"
}
```

### Account Template Example

Create account templates in `test_data/accounts/oracle_account.json`:

```json
{
  "account": {
    "class_fqid": "oracle_account",
    "property_map": {
      "info": {
        "label": {
          "value": "Oracle Test Account"
        }
      },
      "account": {
        "hostname": {
          "value": "{{ORACLE_HOST}}"
        },
        "port": {
          "value": "{{ORACLE_PORT}}"
        },
        "sid": {
          "value": "{{ORACLE_SID}}"
        },
        "username": {
          "value": "{{ORACLE_USERNAME}}"
        },
        "password": {
          "value": "{{ORACLE_PASSWORD}}"
        }
      }
    }
  }
}
```

### Advanced Usage Patterns

#### Template-Based Pipeline Testing

```robot
*** Test Cases ***
Pipeline Template Testing
    [Documentation]    Demonstrates template-based pipeline testing
    [Setup]    Setup Test Environment
    
    ${unique_id}=    Get Time    epoch
    
    # Import pipeline with unique identifier
    Import Pipelines From Template
    ...    ${unique_id}
    ...    ${CURDIR}/pipelines
    ...    ml_oracle
    ...    ML_Oracle_Pipeline.slp
    
    # Create triggered task from template
    ${pipeline_params}=    Create Dictionary    batch_size=500    env=test
    ${notification}=    Create Dictionary    recipients=team@company.com
    
    Create Triggered Task From Template
    ...    ${unique_id}
    ...    /${ORG_NAME}/${PROJECT_SPACE}/${PROJECT_NAME}
    ...    ml_oracle
    ...    ML_Task
    ...    ${pipeline_params}
    ...    ${notification}
    
    # Run task with parameter overrides
    ${new_params}=    Create Dictionary    debug=true    priority=high
    ${payload}    ${job_id}=    Run Triggered Task With Parameters From Template
    ...    ${unique_id}
    ...    /${ORG_NAME}/${PROJECT_SPACE}/${PROJECT_NAME}
    ...    ml_oracle
    ...    ML_Task
    ...    ${new_params}
    
    Log    Job ID: ${job_id}    level=CONSOLE
```

#### Database Integration Testing

```robot
*** Test Cases ***
Database Integration Workflow
    [Documentation]    Tests database connectivity and operations
    
    # Connect to Oracle database
    Connect to Oracle Database
    
    # Create account for database connection
    Create Account From Template    ${CURDIR}/accounts/oracle_account.json
    
    # Execute data pipeline
    ${pipeline_info}=    Import Pipeline
    ...    ${CURDIR}/pipelines/db_integration.slp
    ...    DatabaseIntegrationPipeline
    ...    /${ORG_NAME}/${PROJECT_SPACE}/${PROJECT_NAME}
    
    # Verify pipeline execution
    ${task_response}=    Run Triggered Task
    ...    /${ORG_NAME}/${PROJECT_SPACE}/${PROJECT_NAME}
    ...    DatabaseIntegrationTask
    
    Should Be Equal As Strings    ${task_response.status_code}    200
```

### Utility Keywords

The library also provides utility keywords for common operations:

```robot
# Pretty-print JSON for debugging
Log Pretty JSON    Pipeline Configuration    ${pipeline_payload}

# Wait with custom delays
Wait Before Suite Execution    3    # Wait 3 minutes

# Directory management
Create Directory If Not Exists    ${CURDIR}/output
```

## 🔑 Available Keywords

### SnapLogic APIs
- Pipeline management and execution
- Task monitoring and control
- Data operations and validation

### SnapLogic Keywords  
- High-level business operations
- Pre-built test scenarios
- Error handling and reporting

### Common Utilities
- **Connect to Oracle Database**: Sets up database connections using environment variables
- File operations and data handling
- Environment setup and configuration

## 🛠️ Requirements

- Python 3.12+
- Robot Framework
- Database connectivity libraries
- HTTP request libraries

## 🏗️ Development

```bash
# Clone the repository
git clone https://github.com/SnapLogic/snaplogic-common-robot.git
```

## 🏢 About SnapLogic

This library is designed for testing and automation of SnapLogic integration platform operations.
