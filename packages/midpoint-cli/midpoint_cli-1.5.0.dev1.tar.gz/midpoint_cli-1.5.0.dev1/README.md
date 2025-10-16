# Midpoint CLI

[![PyPI version](https://badge.fury.io/py/midpoint-cli.svg)](https://badge.fury.io/py/midpoint-cli)
[![Python Support](https://img.shields.io/pypi/pyversions/midpoint-cli.svg)](https://pypi.org/project/midpoint-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitLab CI/CD](https://gitlab.com/alcibiade/midpoint-cli/badges/master/pipeline.svg)](https://gitlab.com/alcibiade/midpoint-cli/-/pipelines)
[![Coverage](https://gitlab.com/alcibiade/midpoint-cli/badges/master/coverage.svg)](https://gitlab.com/alcibiade/midpoint-cli/-/commits/master)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

This project is a command line client interface used to drive an Evolveum Midpoint identity management server.

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
  - [Through PyPI](#through-pypi)
  - [Development build](#development-build)
- [Usage](#usage)
  - [General syntax](#general-syntax)
  - [Configuration files](#external-configuration-files-since-v12)
  - [Environment variables](#environment-variables-since-v12)
- [Usage Examples](#usage-examples)
  - [Interactive Mode](#interactive-mode)
  - [User Management](#user-management)
  - [Organization Management](#organization-management)
  - [Task Management](#task-management)
  - [Resource Management](#resource-management)
  - [Scripting and Automation](#scripting-and-automation)
  - [Working with XML Definitions](#working-with-xml-definitions)
  - [Using Configuration Files](#using-configuration-files)
- [Setting up a sandbox environment](#setting-up-a-sandbox-environment)
- [Requirements](#requirements)

## Features

The objectives of this tool are to enable:

* **Administrator access** to run tasks and review data
* **Scripting** for remote controlled automation
* **Test scenarios** implementation

### Core Capabilities

The client currently supports:

* **User Management:** List, search, create, update, and delete users
* **Organizational Units:** Display and manage organizational structures
* **Task Operations:** List tasks with status and duration, run tasks synchronously with progress monitoring
* **Resource Management:** List resources, test connectivity, retrieve configurations
* **Object Operations:** Retrieve, create, update, and delete any Midpoint object type via XML
* **XML Patch Support:** Apply modifications to existing objects using XML patches

### Task Duration Display

* **Running tasks** show real-time elapsed time since start
* **Completed tasks** display total execution time
* Human-readable format (e.g., "2h 35m 20s", "5m 30s", "45s")
* Automatic calculation from Midpoint timestamp fields

### Interactive Mode Features

The strong points of this project are:

* **Dual Execution Modes:** Run commands directly from shell or use an interactive prompt session
* **Colorized Output:** Color-coded output when running in a terminal for improved readability
* **Command History:** Bash-compatible command line history with persistent storage across sessions
* **Tab Completion:** Auto-completion for task names and OIDs
* **Interactive Help:** Full built-in help system with command-specific documentation
* **Standard CLI Syntax:** Classical `midpoint-cli [command] [options]` syntax

### Configuration Flexibility

* **Multiple Auth Methods:** Command-line arguments, environment variables, or configuration files
* **Configuration Priority:** Command-line > Environment variables > Config files > Defaults
* **Secure Credential Storage:** Use config files or environment variables to avoid exposing passwords

## Quick Start

```bash
# Install via pip
pip3 install midpoint-cli

# Check version
midpoint-cli --version

# Start interactive session with credentials via command line
midpoint-cli -u administrator -p password -U https://localhost:8080/midpoint/

# Or run a direct command
midpoint-cli -u administrator -p password -U https://localhost:8080/midpoint/ users

# Use environment variables for authentication (recommended)
export MIDPOINT_URL="https://localhost:8080/midpoint/"
export MIDPOINT_USERNAME="administrator"
export MIDPOINT_PASSWORD="password"

# Now you can run commands without specifying credentials
midpoint-cli
midpoint-cli users
midpoint-cli tasks
```

## Usage

### General syntax

```bash
usage: midpoint-cli [-h] [-v] [-u USERNAME] [-p PASSWORD] [-U URL]
                    [command] [arg [arg ...]]

An interactive Midpoint command line client.

positional arguments:
  command               Optional command to be executed immediately.
  arg                   Optional command arguments.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Show version information
  -u USERNAME, --username USERNAME
                        Set the username to authenticate this session.
  -p PASSWORD, --password PASSWORD
                        Set the password to authenticate this session.
  -U URL, --url URL     Midpoint base URL (e.g., https://localhost:8080/midpoint/)

Available commands:
  get       Get an XML definition from the server from an existing OID reference.
            Usage: get <object-type> <oid>
            Example: get user 12345678-abcd-1234-abcd-123456789012

  put       Create/Update a server object based on an XML structure.
            Usage: put <xml-file>
            Example: put user-definition.xml

  delete    Delete a server object based on its type and OID.
            Usage: delete <object-type> <oid>
            Example: delete user 12345678-abcd-1234-abcd-123456789012

  task      Manage server tasks.
            Subcommands:
              - tasks: List all tasks with status and duration
              - task run <name-or-oid>: Execute a task and wait for completion
            Example: task run "Recompute All Users"

  resource  Manage resources on the server.
            Subcommands:
              - resources: List all configured resources
              - resource test <name-or-oid>: Test resource connectivity
            Example: resource test "Active Directory"

  org       Manage organizations.
            Usage: org [search-term]
            Example: org Engineering

  user      Manage users.
            Subcommands:
              - users: List all users
              - user search <term>: Search for users by name
            Example: user search john
```

### External configuration files (since v1.2)

Settings can be provided from an external configuration file. It can be either:

* .midpoint-cli.cfg in the home directory of the current user
* midpoint-cli.cfg in the current working directory

The syntax is as follows:

```
[Midpoint]
url = https://localhost:8080/midpoint/
username = administrator
password = ...
```

### Environment variables (since v1.2)

The script will scan environment variables to read input parameters. This is
particularly useful for injection of password or in-container execution.

The variables are:

* MIDPOINT_URL
* MIDPOINT_USERNAME
* MIDPOINT_PASSWORD

## Usage Examples

### Interactive Mode

The interactive mode is one of the strongest features of midpoint-cli. It provides a persistent session with command history, tab completion, colorized output, and a built-in help system. This is ideal for exploring your Midpoint server, troubleshooting, and performing multiple operations without re-authenticating.

#### Starting an Interactive Session

```bash
# Start interactive session with authentication
midpoint-cli -u administrator -p mypassword -U https://midpoint.example.com/midpoint/

# Or use environment variables (recommended)
export MIDPOINT_URL="https://midpoint.example.com/midpoint/"
export MIDPOINT_USERNAME="administrator"
export MIDPOINT_PASSWORD="mypassword"
midpoint-cli

# Or use a configuration file
# Create ~/.midpoint-cli.cfg with your credentials
midpoint-cli
```

#### Interactive Features

**Command History Navigation:**
- Use arrow keys (↑/↓) to navigate through command history
- History is persistent across sessions (bash-compatible)
- Search history with Ctrl+R

**Tab Completion:**
- Tab completion available for task names and OIDs
- Complete commands by pressing Tab

**Colorized Output:**
- Automatic color-coded output when running in a terminal
- Improved readability for status indicators and tables

**Built-in Help System:**
```bash
midpoint> help
# Shows all available commands

midpoint> help users
# Shows detailed help for the users command

midpoint> help task
# Shows task-related subcommands and usage
```

#### Common Interactive Workflows

**Exploring Users and Organizations:**
```bash
midpoint> users
# Lists all users with their details

midpoint> user search john
# Search for users matching "john"

midpoint> org
# List all organizational units

midpoint> get user 12345678-abcd-1234-abcd-123456789012
# Get detailed XML definition of a specific user
```

**Task Management Workflow:**
```bash
midpoint> tasks
# View all tasks with status and duration

midpoint> task run "Recompute All Users"
# Execute a task and monitor progress
# For running tasks, duration shows elapsed time
# For completed tasks, duration shows total execution time

midpoint> tasks
# Check updated status after task completion
```

**Resource Testing and Monitoring:**
```bash
midpoint> resources
# List all configured resources

midpoint> resource test "Active Directory"
# Test connectivity to a specific resource

midpoint> tasks
# View any reconciliation tasks that may have been triggered
```

**Quick Object Inspection:**
```bash
midpoint> get user 00000000-0000-0000-0000-000000000002
# Get administrator user definition

midpoint> get task 12345678-task-1234-abcd-123456789012
# Get task details and configuration

midpoint> get resource 12345678-res1-1234-abcd-123456789012
# Get resource configuration
```

#### Interactive vs. Direct Execution

**Interactive mode advantages:**
- No need to re-authenticate for each command
- Command history for repeated operations
- Tab completion for faster input
- Persistent session for exploration
- Better for troubleshooting and manual operations

**Direct execution advantages:**
- Better for scripting and automation
- Can be used in CI/CD pipelines
- Single command operations
- Output can be easily piped to other commands

**Example comparison:**
```bash
# Direct execution - requires full authentication each time
midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/ users
midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/ tasks
midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/ resources

# Interactive mode - authenticate once, run multiple commands
midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/
midpoint> users
midpoint> tasks
midpoint> resources
midpoint> task run "Recompute All Users"
midpoint> tasks
midpoint> exit
```

### User Management

#### List all users

```bash
# Direct command execution
midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/ users

# Output example:
# OID                                   Name           Title           FullName         Status    EmpNo    Email                    OU
# ------------------------------------  -------------  --------------  ---------------  --------  -------  -----------------------  ----
# 00000000-0000-0000-0000-000000000002  administrator                  Administrator    enabled            admin@example.com
# 12345678-abcd-1234-abcd-123456789012  jdoe           IT Manager      John Doe         enabled   E12345   jdoe@example.com         IT
```

#### Search for a specific user

```bash
# Search by name or username
midpoint-cli user search john

# Search with wildcards
midpoint-cli user search "j*"
```

#### Get user details (XML definition)

```bash
# Retrieve full XML definition of a user by OID
midpoint-cli get user 12345678-abcd-1234-abcd-123456789012

# Save user definition to a file
midpoint-cli get user 12345678-abcd-1234-abcd-123456789012 > user-backup.xml
```

#### Create or update a user

```bash
# Upload a user definition from an XML file
midpoint-cli put user-definition.xml

# Update user with a patch file
midpoint-cli put user-patch.xml
```

#### Delete a user

```bash
# Delete a user by OID
midpoint-cli delete user 12345678-abcd-1234-abcd-123456789012
```

### Organization Management

#### List organizational units

```bash
# List all organizational units
midpoint-cli org

# Interactive mode
midpoint> org
# OID                                   Name            Parent    Description
# ------------------------------------  --------------  --------  ---------------------
# 12345678-org1-1234-abcd-123456789012  Engineering     Root      Engineering Department
# 12345678-org2-1234-abcd-123456789012  IT Operations   Root      IT Operations Team
```

#### Get organization details

```bash
# Get full XML definition of an org unit
midpoint-cli get org 12345678-org1-1234-abcd-123456789012
```

### Task Management

#### List all tasks

```bash
# List all tasks with status and duration
midpoint-cli tasks

# Output shows running tasks with elapsed time and completed tasks with total execution time
# Task Name                    Status     Duration    Last Run
# ---------------------------  ---------  ----------  --------------------
# Import from HR System        RUNNING    1h 25m 30s  2025-10-14 10:30:00
# Recompute All Users          CLOSED     5m 42s      2025-10-14 09:15:00
# Reconciliation Task          WAITING    -           Not yet started
```

#### Execute a task synchronously

```bash
# Run a task and wait for completion
midpoint-cli task run "Recompute All Users"

# Run task by OID
midpoint-cli task run 12345678-task-1234-abcd-123456789012
```

#### Get task details

```bash
# Get task status and XML definition
midpoint-cli get task 12345678-task-1234-abcd-123456789012
```

#### Monitor long-running tasks

```bash
# In interactive mode, you can repeatedly check task status
midpoint> task run "Import from HR System"
# Task started: 12345678-task-1234-abcd-123456789012
# Status: RUNNING (Duration: 5m 30s)

midpoint> tasks
# Check all running tasks with real-time duration updates
```

### Resource Management

#### List all resources

```bash
# List configured resources
midpoint-cli resources

# Example output:
# OID                                   Name              Type          Status
# ------------------------------------  ----------------  ------------  --------
# 12345678-res1-1234-abcd-123456789012  Active Directory  LDAP          UP
# 12345678-res2-1234-abcd-123456789012  HR Database       Database      UP
```

#### Test a resource connection

```bash
# Test resource connectivity
midpoint-cli resource test 12345678-res1-1234-abcd-123456789012

# Test by resource name
midpoint-cli resource test "Active Directory"
```

#### Get resource configuration

```bash
# Retrieve full resource definition
midpoint-cli get resource 12345678-res1-1234-abcd-123456789012 > ad-resource.xml
```

### Scripting and Automation

#### Batch operations with scripts

```bash
#!/bin/bash
# Script to backup all users

MIDPOINT_URL="https://midpoint.example.com/midpoint/"
MIDPOINT_USERNAME="administrator"
MIDPOINT_PASSWORD="mypassword"

export MIDPOINT_URL MIDPOINT_USERNAME MIDPOINT_PASSWORD

# Create backup directory
mkdir -p user-backups

# Get list of all users and backup each one
midpoint-cli users | tail -n +3 | while read -r line; do
    OID=$(echo "$line" | awk '{print $1}')
    NAME=$(echo "$line" | awk '{print $2}')

    if [ -n "$OID" ] && [ "$OID" != "----" ]; then
        echo "Backing up user: $NAME ($OID)"
        midpoint-cli get user "$OID" > "user-backups/${NAME}.xml"
    fi
done

echo "Backup completed!"
```

#### Automated user provisioning

```bash
#!/bin/bash
# Create users from a list

MIDPOINT_CLI="midpoint-cli -u admin -p pass -U https://localhost:8080/midpoint/"

# Read user list and create each user
while IFS=',' read -r username fullname email; do
    cat > /tmp/new-user.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<user xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">
    <name>$username</name>
    <fullName>$fullname</fullName>
    <emailAddress>$email</emailAddress>
    <credentials>
        <password>
            <value>ChangeMe123</value>
        </password>
    </credentials>
</user>
EOF

    echo "Creating user: $username"
    $MIDPOINT_CLI put /tmp/new-user.xml
done < users.csv
```

#### Task automation with environment variables

```bash
# Use environment variables for credentials (more secure)
export MIDPOINT_URL="https://midpoint.example.com/midpoint/"
export MIDPOINT_USERNAME="administrator"
export MIDPOINT_PASSWORD="$(cat /secure/location/password.txt)"

# Run tasks without exposing credentials in command line
midpoint-cli task run "Daily User Reconciliation"
midpoint-cli task run "Nightly Cleanup Task"

# Check task status
midpoint-cli tasks | grep -E "RUNNING|RUNNABLE"
```

#### Continuous monitoring script

```bash
#!/bin/bash
# Monitor running tasks and send alerts

while true; do
    RUNNING_TASKS=$(midpoint-cli tasks | grep "RUNNING" | wc -l)

    if [ "$RUNNING_TASKS" -gt 5 ]; then
        echo "WARNING: More than 5 tasks running simultaneously!"
        # Send alert (e.g., via email or Slack)
    fi

    # Check for failed tasks
    FAILED_TASKS=$(midpoint-cli tasks | grep "SUSPENDED")
    if [ -n "$FAILED_TASKS" ]; then
        echo "ALERT: Failed tasks detected:"
        echo "$FAILED_TASKS"
    fi

    sleep 60  # Check every minute
done
```

### Working with XML Definitions

#### Export configuration for version control

```bash
# Export all critical configurations
mkdir -p midpoint-config

# Export resources
midpoint-cli resources | tail -n +3 | while read -r line; do
    OID=$(echo "$line" | awk '{print $1}')
    NAME=$(echo "$line" | awk '{print $2}')
    if [ -n "$OID" ] && [ "$OID" != "----" ]; then
        midpoint-cli get resource "$OID" > "midpoint-config/resource-${NAME}.xml"
    fi
done

# Export roles
midpoint-cli get role 00000000-0000-0000-0000-000000000004 > midpoint-config/superuser-role.xml

# Commit to version control
git add midpoint-config/
git commit -m "Backup Midpoint configuration"
```

#### Apply patches to objects

```bash
# Create a patch file to modify a user
cat > user-patch.xml <<EOF
<?xml version="1.0"?>
<objectModification xmlns="http://midpoint.evolveum.com/xml/ns/public/common/api-types-3">
    <oid>12345678-abcd-1234-abcd-123456789012</oid>
    <modificationType>modify</modificationType>
    <itemDelta>
        <modificationType>replace</modificationType>
        <path>emailAddress</path>
        <value>newemail@example.com</value>
    </itemDelta>
</objectModification>
EOF

# Apply the patch
midpoint-cli put user-patch.xml
```

### Using Configuration Files

Create a configuration file for different environments:

**~/.midpoint-cli.cfg** (Production):
```ini
[Midpoint]
url = https://midpoint.production.example.com/midpoint/
username = automation-user
password = secure-production-password
```

**./midpoint-cli.cfg** (Development - overrides home directory config):
```ini
[Midpoint]
url = https://localhost:8080/midpoint/
username = administrator
password = 5ecr3t
```

Then simply run commands without authentication parameters:

```bash
# Uses configuration from file
midpoint-cli users
midpoint-cli tasks
midpoint-cli resource test "AD Resource"
```

## Requirements

This program is compatible with Python version 3.8 or above.

## Installation

### Through PyPI

The most common way to install midpoint-cli on your own computer is to use the PyPI repository:

```bash
pip3 install midpoint-cli
```

The installation will automatically install all required dependencies including:
- `requests` for HTTP communication
- `tabulate` for formatted table output
- `args` for argument parsing

### Development build

Dependency management, build and test is managed using Python Poetry.

To install Poetry, please refer to [the official Python Poetry website](https://python-poetry.org/).

To install the current development version from GIT:

```bash
yk@lunar:~/dev$ git clone https://gitlab.com/alcibiade/midpoint-cli.git
Cloning into 'midpoint-cli'...
remote: Enumerating objects: 374, done.
remote: Counting objects: 100% (374/374), done.
remote: Compressing objects: 100% (176/176), done.
remote: Total 374 (delta 229), reused 299 (delta 175)
Receiving objects: 100% (374/374), 62.84 KiB | 0 bytes/s, done.
Resolving deltas: 100% (229/229), done.

yk@lunar:~/dev$ poetry install 
Creating virtualenv midpoint-cli-54EjqR0S-py3.12 in /home/yk/.cache/pypoetry/virtualenvs
Updating dependencies
Resolving dependencies... (5.1s)

Package operations: 13 installs, 0 updates, 0 removals

  - Installing args (0.1.0)
  - Installing certifi (2024.8.30)
  - Installing charset-normalizer (3.3.2)
  - Installing idna (3.10)
  - Installing iniconfig (2.0.0)
  - Installing packaging (24.1)
  - Installing pluggy (1.5.0)
  - Installing urllib3 (2.2.3)
  - Installing pytest (8.3.3)
  - Installing requests (2.32.3)
  - Installing tabulate (0.9.0)
  - Installing unidecode (1.3.8)

Writing lock file

Installing the current project: midpoint-cli (1.4.0.dev2)
                
yk@lunar:~/dev$ poetry run midpoint-cli --version
Midpoint CLI Version 1.4.0.dev2

```

### Anaconda

Anaconda packages are not available yet.

## Setting up a sandbox environment

If you wish to test this project locally and don’t have a midpoint server available, you can use the
following instructions.

### Using the Evolveum managed Docker image

Pull the image locally:

```bash
yk@lunar:~$ docker pull evolveum/midpoint
Using default tag: latest
latest: Pulling from evolveum/midpoint

[...]

Digest: sha256:1e29b7e891d17bf7b1cf1853c84609e414c3a71d5c420aa38927200b2bdecc8e
Status: Downloaded newer image for evolveum/midpoint:latest
docker.io/evolveum/midpoint:latest


```

Then run the server and bind the port 8080:

```bash
yk@lunar:~$ docker run -d --name midpoint-1 -p8080:8080 evolveum/midpoint
c048d519395ca48c8e94e361a2239b1c35c5e5305a29600895056e030d6a576f

yk@lunar:~$ midpoint-cli
Welcome to Midpoint client ! Type ? for a list of commands
midpoint> users
OID                                   Name           Title    FullName                Status    EmpNo    Email    OU
------------------------------------  -------------  -------  ----------------------  --------  -------  -------  ----
00000000-0000-0000-0000-000000000002  administrator           midPoint Administrator  enabled
midpoint>

yk@lunar:~$ docker stop midpoint-1
midpoint-1
```
