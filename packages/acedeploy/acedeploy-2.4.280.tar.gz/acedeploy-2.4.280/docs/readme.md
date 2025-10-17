- [Acedeploy](#acedeploy)
  - [Technology](#technology)
  - [How it works](#how-it-works)
  - [Features](#features)
    - [Deployment modes](#deployment-modes)
    - [Supported objects](#supported-objects)
    - [Pre- and postdeployment scripts](#pre--and-postdeployment-scripts)
    - [SQL variables](#sql-variables)
    - [String replacement in DDLs](#string-replacement-in-ddls)
  - [Operation details](#operation-details)
    - [Consideration on object updates](#consideration-on-object-updates)
    - [Altering Pipes](#altering-pipes)
    - [Altering Tasks](#altering-tasks)
    - [Creating and altering External Tables](#creating-and-altering-external-tables)
    - [Policies references](#policies-references)
      - [Default Policy reference handling](#default-policy-reference-handling)
        - [Policies applied on objects from outside the deployment process](#policies-applied-on-objects-from-outside-the-deployment-process)
        - [Policies applied on objects by the deployment process](#policies-applied-on-objects-by-the-deployment-process)
      - [Reapply existing policies on views after deployment](#reapply-existing-policies-on-views-after-deployment)
      - [Manage policy assignments in DDLs](#manage-policy-assignments-in-ddls)
      - [Cloe policy extension](#cloe-policy-extension)
    - [Rollback](#rollback)
    - [Quoted identifiers](#quoted-identifiers)
    - [Object options](#object-options)
    - [Known limitations and Bugs](#known-limitations-and-bugs)
    - [Tested and untested configurations](#tested-and-untested-configurations)
- [Additional tools and extensions](#additional-tools-and-extensions)
- [Static DDL checks](#static-ddl-checks)
- [Technical information](#technical-information)
    - [File and folder structure](#file-and-folder-structure)
  - [Deployment settings](#deployment-settings)
  - [Technical details](#technical-details)
- [Quickstart](#quickstart)

# Acedeploy

Acedeploy is a tool to deploy SQL objects to a Snowflake database.
It is best used in a CI/CD workflow, but can be run locally as well.
Acedeploy uses an declarative approach.
Developers create DDLs describing the desired properties of the database objects (tables, views, procedures,... ), i.e. they write CREATE statements only.
When deploying to a database, Acedeploy will generate the required ALTER statements.
Unlike in an imperative approach, the developers will not be writing ALTER statements.

## Technology

Acedeploy is built with Python 3.11.11.
All of Acedeploy's dependencies are available via the Python Package Index (pypi.org).
The full list is found in `requirements.txt`.

Extensions and tools might have additional dependencies.
See descriptions [here](tools.md).

## How it works

![basic deployment process](figures/deployment_basic.png "basic deployment process")

Basic overview of deployment steps:
1)	Analyze the files in the repository. Each SQL DDL is parsed to determine the object type and any dependencies this object has on other objects. Knowing the dependencies is crucial to determine the order in which the objects need to be created.
2)	Deploy the objects to a temporary database. Either the complete solution can be deployed or only the changes since the last deployment. If only the changes are deployed, the runtime of the deployment can be significantly reduced, depending on the size of the solution. If the validation fails, the developer receives feedback from Ace Deploy that, for example, syntax or referencing errors are the cause.
3)	Query the metadata from the temporary database and the target database for all objects. Then, compare the metadata to determine the SQL statements that need to be executed to get the target database into the desired state. For objects containing (meta-)data, ALTER statements are generated.
4)	Execute the SQL statements on the target database. Dependent views are also updated, if necessary, so that they have the latest metadata information. If the deployment fails, an automated rollback can restore the state before the deployment.

## Features

### Deployment modes

These deployment modes (setting `deploymentMode`) exist:

- Validation: Deploy solution to an empty temporary database to see if the solution is valid. After validation, the database will be dropped.
- Develop: Deploy the solution to a target database.
- Release: Clone the target database, deploy the solution to a target database, roll back if deployment fails.

For all modes, you can choose to deploy (setting `solutionOptions/ignoreGitInformation`):

- The full solution
- Only changes made in git since a given git tag (setting `solutionRepoTagRegex`). This allows a faster deployment to large databases.

Optionally, you can choose to deploy to a clone of the target database, instead of the target database itself (setting `cloneOptions/deployToClone`).
This is useful to check if the current solution in a repository is compatible with the target database (e.g. to see if data would be lost during deployment).

### Supported objects

These type of objects are supported.
All other types are not supported.

- SCHEMA
- TABLE
- EXTERNAL TABLE
- VIEW
- MATERIALIZED VIEW (not supported on Snowflake Standard edition accounts)
- FUNCTION
- PROCEDURE
- FILE FORMAT
- STAGE
- STREAM
- TASK
- PIPE
- SEQUENCE
- MASKING POLICIES (not supported on Snowflake Standard edition accounts)
- ROW ACCESS POLICIES (not supported on Snowflake Standard edition accounts)
- TAGS (not supported on Snowflake Standard edition accounts)
- DYNAMIC TABLE
- NETWORK RULE

### Pre- and postdeployment scripts

Pre- and postdeployment scripts are executed before or after a deployment.
These SQL scripts can be used to implement changes that are not directly supported by Acedeploy.
For details, see [here](deployment_settings.md).

### SQL variables

SQL variables (https://docs.snowflake.com/en/sql-reference/session-variables.html) can be set for the deployment using `deployment.json`.
They apply for the deployment of all objects and pre/postdeployment steps.
For details, see [here](deployment_settings.md).

### String replacement in DDLs

It is possible to replace strings in DDLs and pre/postdeployment steps during loading of the solution.
This can be useful if some values need to be switched out where it is currently not possible with SQL variables.
__Beware:__
String replacement increases the danger of SQL injection.
Use with caution.
For details, see [here](deployment_settings.md).

## Operation details

### Consideration on object updates

If the framework detects that the database differs from the solution, it will update differing objects, if required.
Depending on type, objects are treated differently.

The following objects are updated on the target database if they are deployed to the meta database.
Metadata information for these objects will not be used to determine if they need to be redeployed to the target database.
For a full deployment, all of these objects will always be updated on the target database.
For a git-diff deployment, these objects will be deployed if there was a git change to the file.
The objects will always be created with `CREATE OR REPLACE`.
- MATERIALIZED VIEW
  -  Be aware that the query in the definition will be executed in order to create the materialized view. Depending on size of the query and size of the current warehouse, this can be a lengthy operation.
- FUNCTION
  - parameter default values are allowed, but cannot contain nested brackets, e.g. this is **not** allowed: `substr(upper('my string'), 1, 2)`
- PROCEDURE
  - same limitation on parameter defaults as FUNCTION
- TASK
- EXTERNAL TABLE

The following objects are updated only when metadata differences are detected.
Updates are performed with one or more `ALTER <object>` statements, unless noted otherwise:
- SEQUENCE
  - COMMENT
  - INCREMENT
- STREAM
  - COMMENT
- TABLE
  - COLUMNS
    - COMMENT
    - NULLABILITY
    - change n in NUMBER(n, m)
    - increase n in VARCHAR(n)
    - DROP DEFAULT
    - change DEFAULT from one sequence to another sequence
    - TAG
  - COMMENT
  - DATA_RETENTION_TIME_IN_DAYS
    - this will only be set if it is different from the value currently set on the schema
  - Constraints (PRIMARY KEY, UNIQUE, FOREIGN KEY)
    - If a change on a table constraint is detected, all constraints of that type on that table will be dropped and recreated (this might change system generated constraint names)
    - Constraint properties (such as ENFORCED, DEFERRABLE and others) will be deployed to Snowflake when the table is first created. These properties will not be updated in susequent deployments.
  - CLUSTER KEY
  - TAG
  - policy references for ROW ACCESS POLICY
    - If a row access policy that is part of the solution is applied to the table, this reference can by managed by the deployment.
- VIEW
  - Will be update with `CREATE OR REPLACE` any difference is detected
- POLICY (MASKING POLICY and ROW ACCESS POLICY):
  - COMMENT
  - BODY
- PIPE
  - COMMENT
  - other changes via `CREATE OR REPLACE`, see section Altering Pipes
- STAGE
  - COMMENT
- FILE FORMAT
  - COMMENT
  - all `format_options` returned by `SHOW FILE FORMATS`, except `TYPE` and `VALIDATE_UTF8`.
- SCHEMA
  - COMMENT
  - DATA_RETENTION_TIME_IN_DAYS
    - this will only be set if it is different from the value currently set on the database

Any properties not listed above can not be updated. Once an object has been created, new deployments will not affect those properties.

Make sure that for objects updated with `CREATE OR REPLACE`, the permissions are preserved (e.g. by making use of `GRANT <permission> ON FUTURE OBJECTS IN SCHEMA <schema>;`)

### Altering Pipes

Most properties of pipes cannot be changed via ALTER PIPE (except COMMENT).
For thoses properties, we need to execute CREATE OR REPLACE PIPE.
In order not to interrupt any active loading processes, the framework will pause any running pipes that need to be replaced.

Steps during deployment:
1. Get current executionState during get metadata step
1. (Compare metadata, determine required actions, create rollback clone, order actions, generate statements)
1. Pause pipe execution if the pipe is running
  - Check if pausing was successful, if not, raise exception
  - Check if pending files is 0, if not, raise exception
1. Create or replace pipe during deployment
1. If executionState was not RUNNING before deployment, pause the pipe directly after create or replacing the pipe

### Altering Tasks

- Snowflake does not check the definition of tasks before creating them. You need to manually validate that the tasks work.
- New tasks will be created in suspended state and need to be started either manually or with a postdeployment step.
- Dropping tasks might fail the deployment, unless the root task of the tree has been suspended prior to deployment (either manually or with a predeployment step).
- If a task is updated, the default is that _all_ tasks in that tree will be suspended after the deployment. If you want the tasks to have the same state as they did before the deployment, set the deployment option `resumeTasks` to `true`, see [here](deployment_settings.md).

### Creating and altering External Tables

External tables can only be created if the referenced files can be accessed and match the external table definition.
If the files do not yet exists or can not be accessed (e.g. if the stage is not allowed to access the files), the external table creation or update will fail.
Therefore, a change in a storage account can potentially disrupt the deployment.

In addition, queries on the view INFORMATION_SCHEMA.EXTERNAL_TABLES can be very slow.
Acedeploy needs to query the view to manage external tables, so this might slow down the deployment.

### Policies references

There are multiple options to handle policies assignments using acedeploy. You may only chose one option.

#### Default Policy reference handling

**We do not recommend using the default behavior.**

If no options are specified, the following applies:

##### Policies applied on objects from outside the deployment process

If a process other than an Acedeploy deployment applied masking policies or row access policies on objects maintained by Snowflake, these options exist:
- If the object is a table, Acedeploy will alter the table which keeps existing policies. (Keep in mind that pre/postdeployment script might still replace a table, which will remove any existing policy.)
- If the object is a view there are two options:
  - default: The view is replaced, which removes any policies.
- Reapplying policies to materialized views is not supported. Redeploying a materialized view with an applied policy will remove that policy.


##### Policies applied on objects by the deployment process

Snowflake allows assigning policies in a DDL statement.
Acedeploy supports assigning policies in the DDL of a view.
*Assigning policies on tables in a DDL statement this way is not fully supported.*
If a policy is applied to a table in the DDL statement the following applies:
- If the table is newly created on the target database, it will have the policies as defined in the DDL.
- If the policy definition in the DDL statement is changed or deleted, these changes will not be applied to the target database. DDL on the target database and the solution will diverge from that point on.

Avoid using policies in CREATE TABLE definitions, or always remember to manually add these changes using a pre- or postdeployment script.

#### Reapply existing policies on views after deployment

**This option is deprecated and might be removed in a future release.**

In `deployment.json`, set `deploymentOptions.reapplyExistingPolicies=true`: Replace the view during. If policies were applied to the view, apply them immediately after replacing the view. This requires querying the applied policies before deployment. **This query is inefficient and might take very long for large databases.** The process will check if all requried columns of that policy are still available in the updated view. **A change in datatype of a column with an applied policy will not be noticed before deployment and will likely cause the deployment to fail.** The role with which the deployment is executed must have sufficient priviledges: OWNERSHIP on the VIEW and APPLY on any referenced POLICY.

In order for this process to work, the role executing the deployment should have `OWNERSHIP` on the view and `APPLY` on the policies.

#### Manage policy assignments in DDLs

**Currently only supported for row access policies and masking on tables.**

Create both the policy and the table using acedeploy. In the table ddl, you can use standard snowflake syntax to assign a policy (e.g. `CREAET TABLE x.y (...) WITH ROW ACCESS POLICY a.b ON (...)`).

To enable this behavior, set the appropriate values (e.g. `manageRowAccessPolicyReferences`, `manageMaskingPolicyReferences`) in the object's option in `deployment.json` to `true`.

#### Cloe policy extension

Configure and control policies assignments from an external location. Configured with `policyHandlingCloeExtension`.

For details, refer to https://dev.azure.com/initions-consulting/CLOE/_git/cloe-extensions-snowflake-policies-py.

### Rollback

The deployment framework features a rollback mechanism, which automatically starts if a deployment in mode `release` fails due to a deployment problem.
(The rollback can not undo a sucessful deployment. For that, create a new deployment.)
Before executing the deployment, a clone of the target database is created.
If the deployment fails, all objects that have already been updated on the target database will be replaced by the objects that were previously cloned.
Be aware that this might revert data loaded into tables during the deployment.

In case of a rollback, these objects will be skipped:
  - Tasks (cannot be renamed)
  - Streams (cannot be renamed)
  - Stages (internal stages cannot be cloned and we do not check whether a stage is internal or external)
  - Pipes (pipes can only be cloned if they do not reference an internal stage)
  - Sequences (if sequences were a part of rollback, tables with references to sequences would refer to original sequence instead of rolled back sequence)

Pre/Postdeployment scripts and rollback:
  - Clone to be used in case of rollback is created after successful predeployment
  - Clone to be used in case of rollback is dropped before postdeployment
  - Consequentially, failure of a pre- or postdeployment script will not trigger a rollback
  - In case of rollback, any changes due to predeployment scripts will not be rolled back

### Quoted identifiers

The deployment framework does not support object identifiers that require double quotes (https://docs.snowflake.com/en/sql-reference/identifiers-syntax.html).
Object names in DDLs can still be written in double quotes, but they should only contain the characters A-Z, underscore ("_") and numbers.
When the Snowflake parameter `QUOTED_IDENTIFIERS_IGNORE_CASE` is set to `FALSE`, object names in double quotes **must** be written in upper case.

Examples:
```SQL
CREATE TABLE MY_SCHEMA.MY_TABLE ... -- ok
CREATE TABLE "MY_SCHEMA"."MY_TABLE" ... -- ok
CREATE TABLE "my_schema"."my_table" ... -- ok, if QUOTED_IDENTIFIERS_IGNORE_CASE = TRUE
CREATE TABLE "my_schema"."my_table" ... -- not supported, if QUOTED_IDENTIFIERS_IGNORE_CASE = FALSE
CREATE TABLE "MY-SCHEMA"."MY-TABLE" ... -- not supported (contains character "-")
```

These limitations apply to all identifiers, e.g. database names, schema names, table names, table columns, table constraints, function parameters.
They apply to all objects that are part of the solution.
Additionally, there can not be any schemas which require quoted identifiers on the target database, even if these schemas are not part of the solution managed by the framework.

### Object options

Options can be set per SQL object type (e.g. TABLE, VIEW, ...).

- All objects support `enabled`, which defaults to `true`. By setting this value to `false`, that object type can not be created. This is useful for excluding object types you do not wish to deploy. **Recommendation**: Set this value to `false` for `EXTERNAL TABLE` if you do not want to deploy external tables. Querying metadata for external tables can be very slow, which can be avoided by excluding them from the deployment.
- `manageTagAssignments` is allowed for `TABLE`, `EXTERNAL TABLE`, `VIEW`,  `MATERIALIZED VIEW`, `DYNAMIC TABLE` and manages tag assignments for these objects. Querying tag assignments might be inefficient and increase deployment time.
- All objects support `metadataOptions`, which gives control over the metadata used for deployments. The default is to use all available metadata. Each entry in `metadataOptions` must be an existing metadata field for that object type, e.g. `COMMENT`. (We currently do not have a list of possible values, sorry.) Each objects expects a dictionary of options. The only allowed option is `ignore` (defaults to `False`). Example: `{"TABLE": {"metadataOptions"}: "COMMENT": {"ignore": True}}`.
  - Additionally, if the metadata field is `COLUMN_DETAILS`, a subproperty can be targeted, e.g. `{"TABLE": {"metadataOptions"}: "COLUMN_DETAILS": {"IDENTITY_START": {"ignore": true}, "IDENTITY_INCREMENT": {"ignore": true}}}`
  - This functionality has only been tested for `TABLE.COLUMN_DETAILS.IDENTITY_START` and `TABLE.COLUMN_DETAILS.IDENTITY_INCREMENT`. Other properties might yield errors or unexpected results.
- `manageTagAssignments` is allowed for `TABLE`, `EXTERNAL TABLE`, `VIEW`,  `MATERIALIZED VIEW` and manages tag assignments for these objects. Querying tag assignments might be inefficient and increase deployment time.
- `manageRowAccessPolicyReferences` is allowed for `TABLE` and manages references of row access policies for these objects. Querying policy references might be inefficient and increase deployment time.
- `disabledLanguages` is allowed for `PROCEDURE`, `FUNCTION` to set language restrictions for Stored Procedures (key-word "PROCEDURE") and User-Defined-Functions (key-word "FUNCTION") -> supported values are: "PYTHON", "JAVA", "JAVASCRIPT", "SCALA", "SQL". Note: Input type is a list/array of disabled languages.
- `dropOverloadedObjects` is allowed for `PROCEDURE`, `FUNCTION` to drop overloaded procedures/functions (with the same name and same reference) before deployment. This option can be used to avoid errors when deploying overloaded procedures/functions e.g. when adding default values for input parameters which can lead to the error "Cannot overload PROCEDURE 'MYPROC' as it would cause ambiguous PROCEDURE overloading.".
- `alterOptions` for `TABLE`:
  - `keepColumnOrder` (bool): If new columns are added within the list of existing columns, either, raise an error (if `createAndInsert.enabled = False`), or use `createAndInsert` (if `createAndInsert.enabled = True`).
  - `createAndInsert`: Instead of ALTER TABLE, this functionality will CREATE a (temporary) TABLE with the desired structure, INSERT data from the original TABLE and SWAP the two tables. This functionality is used when a column is added in between existing columns and `keepColumnOrder = True`. Settings below can add additional conditions under which this functionality is used.
    - `enabled` (bool): Enable this functionality.
    - `dropOldTable` (bool): After swapping the tables, drop the original table. Otherwise, it will remain in place.
    - `useAsFallback` (bool): If, for any reason, no valid alter statements can be generated for the table, use create and insert instead.
    - `updateAutoincrement` (bool): If any column in the table use a AUTOINCREMENT, the new table will have set the starting index set to the next value (max value + increment if increment is positive, otherwise min value + increment if increment is negative). **This might lead to issues with future deployments, as the object in the database no longer matches the DDL defintion. It is adviced to update the DDL afterwards to match the new starting index.**
    - `warehouses` (list): Since the INSERT operation can be resource intensive, you can choose to use other warehouses for this operation. The warehouse is determined by the byte size of the table
      - `byteThreshold`: From this list, we pick the warehouse that has the smalles threshold set that is above the tables byte size.
      - `name`: Name of the warehouse.


### Known limitations and Bugs

- File names must end with `.sql`.
- Handling of file formats is not perfect. Make sure to use UTF8.
- Placing more than one SQL statement in a single file is not possible.
- Views with implicit joins on stages are not supported (e.g. `SELECT A.$1, B.$2 FROM @S.STAGE1 A, @S.STAGE2 B`). Use CTEs instead.
- Each deployment can only deploy objects to a single database at a time. (Ideally, there should be no objects in the database that reference another database.)
- If `DATA_RETENTION_TIME_IN_DAYS` is set on a table and it has the same value on the containing schema, the value will be unset. Only when the values are different will they be set on the table. The same applies for the a schema and the containing database.
- A column default with AUTOINCREMENT can not be removed by the framework
  - Recommendation: Instead of AUTOINCREMENT, use a sequence if possible. Sequences can be updated after initial deployment
  - Recommendation: If you need to remove AUTOINCREMENT on a column, use a predeploymentscript: `ALTER TABLE x.y ALTER COLUMN z DROP DEFAULT`
  - Additional information: AUTOINCREMENT in Snowflake can only be removed, never added to a column. AUTOINCREMENT properties in Snowflake (START, INCREMENT) cannot be updated after column creation.
- Dropping a column referenced in a foreign key in another table will result in error. To avoid this error:
  - either: drop foreign key constraint in a first deployment, then, in a separate deployment, drop the column containing the column
  - or: drop the foreign key constraint using a predeployment script
- Creating a clone to deploy solution on with settings `cloneOptions.deployToClone=true, cloneMode=minimal` will fail and will default back to `cloneOptions.deployToClone=true, cloneMode=schemaList` in these instances:
  - Stages are part of the solution (Reason: GET_DDL() not supported for stages)
  - Transient tables are part of the solution (Reason: transient tables cannot be cloned into permanent tables. In the current implementation, we cannot tell them apart.)
  - Streams are part of the solution (Reason: GET_DDL() removes schema reference for accessed tables)
- database repo compare:
  - excludes schemas
  - excludes stages (Reason: GET_DDL() not supported for stages)
  - will not show details on differences in constraints (if a constraint differs, it will cause the an entry to appear in the list, but details will not be displayed)


### Tested and untested configurations

Considered to work well:

- Deployment (all modes) using **git diff** since last tagged commit. Pre- and Postdeployment steps will only be executed if they have been changed or added since the last tagged commit.
- Deployment (all modes) using **full solution**, but without the use of pre- and postdeployment steps.

Untested:

- Deployment using full solution including pre- and postdeployment steps.
- Option `dropTargetObjectsIfNotInProject` is not well tested.


# Additional tools and extensions

The acedeploy-framework Python package also includes a set of tools.
They include
- a tool to compare any given database to a given set of SQL DDLs
- a set of tools to clone parts of databases or full databases
- a tool to run a basic smoketest after a successful deployment
- a tool to analyse a given set of files and export dependencies of objects (e.g. which view depends on which table)

A full list and description is given [here](tools.md).


# Static DDL checks

In order to validate that all SQL files are in the correct format, we recommend to run static DDL checks against all files.
A set of pytests is given in `pytest/ddl-check-technical`.

# Technical information

### File and folder structure

File and folder structure is no longer required.
The framework extracts types and names directly from the files now.
The folder structure shown below is still best practice.

The DDLs is recommended be organized as follows: Every name of a subfolder is a schema name of the target database (the whole word in uppercase). Within that folder, the schema definition (with the same file name) and the objects (object type with capital first letter) are located. Compare this example:
- myProject
  - SCHEMA1
    - Tables
      - schema1.table1.sql
      - schema1.table2.sql
      - ...
    - Views
      - schema1.view1.sql
      - schema1.view2.sql
      - ...
    - Procedures
      - schema1.procedure1.sql
      - schema1.procedure2.sql
      - ...
    - schema1.sql
  - SCHEMA2
    - Tables
      - schema2.table1.sql
      - schema2.table2.sql
      - ...
    - Views
      - schema2.view1.sql
      - schema2.view2.sql
      - ...
    - Procedures
      - schema2.procedure1.sql
      - schema2.procedure2.sql
      - ...
    - schema2.sql
  - ...


## Deployment settings

A detailed description of the settings in `deployment.json` is found [here](deployment_settings.md).

## Technical details

- [Technical description of workflow, classes and methods](workflow_classes_methods.md)

# Quickstart

You can use an existing solution for this, or create a small example yourself.
In the example below, we use MINIMAL_EXAMPLE solution.

First, set up `deployment.json`.
Example:

```JSON
{
    "$schema": "../../resources/json-schemas/deployment.schema.json",
    "deploymentMode": "develop",
    "releaseName": "my_test_release",
    "solutionRepoTagRegex": "^v[0-9]+$",
    "solutionOptions": {
        "ignoreGitInformation": false,
        "dropTargetObjectsIfNotInProject": false,
        "stopAtDataLoss": true
    },
    "cloneOptions": {
        "deployToClone": false,
        "cloneMode": "full",
        "dropCloneAfterDeployment": true
    },
    "parallelThreads": 10,
    "keyService": "ENVIRONMENT",
    "targetOptions": {
        "metaDatabase": "MY_META_DB",
        "account": "ab12345.west-europe.azure",
        "login": "U_PIPELINE",
        "password": "@@SNOWFLAKE_PASSWORD@@",
        "role": "SYSADMIN",
        "warehouse": "COMPUTE_WH",
        "targetDatabase": "MY_TARGET_DB",
        "projectFolder": "examples/solutions/MINIMAL_EXAMPLE",
        "projectSchemas": {
            "blacklist": []
        },
        "preDeploymentSettings": [
          {
            "path": "examples/solutions/MINIMAL_EXAMPLE/_static_predeployment",
            "type": "folder",
            "condition": "always"
          },
          {
            "path": "examples/solutions/MINIMAL_EXAMPLE/_predeployment",
            "type": "folder",
            "condition": "onChange"
          }
        ],
        "postDeploymentSettings": [
          {
            "path": "examples/solutions/MINIMAL_EXAMPLE/_static_postdeployment",
            "type": "folder",
            "condition": "always"
          },
          {
            "path": "examples/solutions/MINIMAL_EXAMPLE/_postdeployment",
            "type": "folder",
            "condition": "onChange"
          }
        ]
    }
}
```

This snippet can be used to start the deployment:

```python
import acedeploy.main as acedeploy_client
import os
import logging
from aceutils.logger import LoggingAdapter, LogFileFormatter, DefaultFormatter

# Set up logging output
logger = logging.getLogger('acedeploy')
logger.setLevel(logging.DEBUG)
log = LoggingAdapter(logger)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(DefaultFormatter())
logger.addHandler(sh)

# Set required environment variables
os.environ['ACEDEPLOY_SOLUTION_ROOT'] = '/workspaces/Acedeploy' # absolute root path of the git repository, also used to as base path for relative paths
os.environ["ACEDEPLOY_CONFIG_PATH"] = '/workspaces/Acedeploy/examples/solutions/MINIMAL_EXAMPLE/deployment.json' # absolute path to deployment.json

# Inject password (for production use, use a suitable method)
os.environ['SNOWFLAKE_PASSWORD'] = '123'

# Start the deployment
config = acedeploy_client.configure()
acedeploy_client.execute_deployment(config)
```
