Fabric task generator for AWS CloudFormation
============================================

A Python library that generates [Fabric](http://www.fabfile.org) tasks to manipulate the stack of AWS CloudFormation.

You will be able to manipulate the CloudFormation stack with the CUI.

```bash
$ fab list_stacks
Stacks:
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
| StackAlias | StackName            |      Status     | DriftStatus |           CreatedTime            | UpdatedTime | Description |
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
| foo        | fabricawscfn-dev-foo | CREATE_COMPLETE |   DRIFTED   | 2017-03-05 04:35:12.823000+00:00 |      -      | Foo bucket. |
| bar        | fabricawscfn-dev-bar |   Not created   |     -       |                -                 |      -      | -           |
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
```

# Setup

## Requirement

* Python 2.x  (**Do not support Python 3.**)
* [Fabric 1.x](http://www.fabfile.org)  (**Do not support Fabric2.**)
* [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-set-up.html)

:bangbang::bangbang:**No plans to support Python 3.x and Fabric 2.x for the following reasons.**:bangbang::bangbang:
* Could not keep concept and compatibility.
* Keyword args can not be use for task parameter.

Recommended to switch Python environment using [pyenv](https://github.com/pyenv/pyenv) etc.


## Install

Install `fabricawscfn` (and [Dependencies](./setup.py)) via pip.

```bash
pip install fabricawscfn

 OR

pip install git+https://github.com/crossroad0201/fabric-aws-cloudformation.git
```

## Update

```bash
pip install fabricawscfn -U

 OR

pip install git+https://github.com/crossroad0201/fabric-aws-cloudformation.git -U
```

## Uninstall

```bach
pip uninstall fabricawscfn
```

# Usage

Local directory and file structure example.
```text
fabfile.py
templates/
  - foo.yaml
  - subdir/
    - bar.yaml
```

See [Example fabfile.py](./example/fabfile.py).

## 1.Preparation

* Create **S3 bucket** for store CloudFormation templates.

## 2.Import Fabric AWS CloudFormation.

Import `fabricawscfn` in your `fabfile.py`.

```python
from fabricawscfn import *
```

## 3.Define stacks and generate Fabric tasks.

```python
StackGroup('my-cfn-templates', 'example', 'templates')\
  .define_stack('foo', 'example-foo', 'foo.yaml')\
  .define_stack('bar', 'example-bar', 'subdir/bar.yaml', Tags=[{'Key':'example', 'Value':'EXAMPLE'}])\
  .generate_task(globals())
```

### 3-1.Create StackGroup

Instantiate `StackGroup`.

* Parameters.
  * `templates_s3_bucket` - Prepared S3 bucket name.
  * `templates_s3_prefix` - Prefix(Folder) name in prepared S3 bucket. CloudFormation templates store in.
  * `templates_local_dir` - **OPTIONAL:** Local dir(relative path) where CloudFormation template(s) location.

* `templates_s3_bucket` and `templates_s3_refix` can contains placeholder(Like this `foo-%(environment)s`). Replace by Fabric env.

* **OPTIONAL:** You can specify default AWS region and account if necessary.
  * Default, use AWS credentials default profile.
  * You can override it, use `region` and `account` task.

```python
StackGroup(...)\
  .region('us-west-2')\
  .account('ACCESS_KEY_ID', 'SECRET_ACCESS_KEY')\
    :
```

### 3-2.Define Stack

Define Stack(s) using `StackGroup#define_stack()`.

* Parameters.
  * `alias` - Alias(Short name) of Stack. This name using task parameter.
  * `stack_name` - CloudFormation Stack name.
  * `template_path` - Template file path.(Relative path from `templates_local_dir`)
  * `**kwargs` - **OPTIONAL:** Additional arguments for Create/Update/Delete stack. See [Boto3 reference](https://boto3.readthedocs.io/en/latest/reference/services/cloudformation.html#CloudFormation.Client.create_stack).
    * If you want to set default stack arguments for all stacks, using `StackGroup#default_stack_args()`.

* `stack_name` can contains placeholder(Like this `foo-%(environment)s`). Replace by Fabric env.

### 3-3.Generate Task

Generate Fabric tasks using `StackGroup#generate_task()`.

* Parameters.
  * `namespace` - Generated tasks added to this namespace. Normaly specify `globals()`.

## 4.Finish

You can check generated tasks run `fab -l` command.

```bash
$ fab -l

Example fabfile.py using fabricawscfn.

Available commands:

    account            Set AWS account. (Default use AWS credentials default ...
    console            Open AWS Console on your default Web browser.
    create_bar         create stack bar.
    create_foo         create stack foo.
    delete_bar         delete stack bar.
    delete_foo         delete stack foo.
    desc_stack         Describe existing stack.
    detect_drift       List detected drifts. (Different resource property between Stack and Actual resource).
    dryrun             Turn on DRY-RUN mode for create_xxx, update_xxx task.
    env_on             Set environment.(Default dev)
    list_exports       List exports.
    list_resources     List existing stack resources.
    list_stacks        List stacks.
    params             Set parameters. (Applies to all tasks)
    profile            Set AWS Profile. (Default use AWS credentials default profile)
    region             Set AWS Region. (Default use AWS credentials default p...
    sync_templates     Synchronize templates local dir to S3 bucket.
    update_bar         update stack bar.
    update_foo         update stack foo.
    validate_template  Validate template on local dir.
```

# Tasks

Show available all tasks run `fab -l`, and more detail `fab -d [TASK_NAME]`.

## Basic Tasks.

### `list_stacks`

Show stacks list.

```bash
$ fab list_stacks
Stacks:
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
| StackAlias | StackName            |      Status     | DriftStatus |           CreatedTime            | UpdatedTime | Description |
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
| foo        | fabricawscfn-dev-foo | CREATE_COMPLETE |   DRIFTED   | 2017-03-05 04:35:12.823000+00:00 |      -      | Foo bucket. |
| bar        | fabricawscfn-dev-bar |   Not created   |     -       |                -                 |      -      | -           |
+------------+----------------------+-----------------+-------------+----------------------------------+-------------+-------------+
```

### `desc_stack:[StackAlias or StackName]`

Show stack detail.

```bash
$ fab desc_stack:foo
Stack:
+----------------------+-----------------+-------------+----------------------------------+-------------+----------------------------------+-------------+
| StackName            |      Status     | DriftStatus |           CreatedTime            | UpdatedTime |        DriftDetectedTime         | Description |
+----------------------+-----------------+-------------+----------------------------------+-------------+----------------------------------+-------------+
| fabricawscfn-dev-foo | CREATE_COMPLETE |   DRIFTED   | 2017-03-05 04:35:12.823000+00:00 |      -      | 2017-03-05 04:35:12.823000+00:00 | Foo bucket. |
+----------------------+-----------------|-------------+----------------------------------+-------------+----------------------------------+-------------+
Parameters:
+---------+--------+
| Key     | Value  |
+---------+--------+
| Param4  | PARAM4 |
| Param3  | PARAM3 |
| Param2  | PARAM2 |
| Param1  | PARAM1 |
| EnvName | dev    |
+---------+--------+
Outputs:
+--------+-----------------+-------------+
| Key    | Value           | Description |
+--------+-----------------+-------------+
| Bucket | sandbox-dev-foo | Foo bucket. |
+--------+-----------------+-------------+
Events(last 20):
+----------------------------------+--------------------+----------------------------+----------------------+-----------------------------+
| Timestamp                        |       Status       | Type                       | LogicalID            | StatusReason                |
+----------------------------------+--------------------+----------------------------+----------------------+-----------------------------+
| 2017-03-05 04:35:55.694000+00:00 |  CREATE_COMPLETE   | AWS::CloudFormation::Stack | fabricawscfn-dev-foo |                             |
| 2017-03-05 04:35:53.009000+00:00 |  CREATE_COMPLETE   | AWS::S3::Bucket            | Bucket               |                             |
| 2017-03-05 04:35:32.308000+00:00 | CREATE_IN_PROGRESS | AWS::S3::Bucket            | Bucket               | Resource creation Initiated |
| 2017-03-05 04:35:31.102000+00:00 | CREATE_IN_PROGRESS | AWS::S3::Bucket            | Bucket               |                             |
| 2017-03-05 04:35:12.823000+00:00 | CREATE_IN_PROGRESS | AWS::CloudFormation::Stack | fabricawscfn-dev-foo | User Initiated              |
+----------------------------------+--------------------+----------------------------+----------------------+-----------------------------+
```

### `validate_template:[StackAlias]`

Validate CloudFormation template.

```bash
$ fab validate_template:bar
Validating template templates/subdir/bar.yaml...
[localhost] local: aws cloudformation validate-template --template-body file://templates/subdir/bar.yaml --output table
--------------------------------------------------------------------
|                         ValidateTemplate                         |
+--------------------------------+---------------------------------+
|  Description                   |  Bar bucket.                    |
+--------------------------------+---------------------------------+
||                           Parameters                           ||
|+--------------+----------------------+---------+----------------+|
|| DefaultValue |     Description      | NoEcho  | ParameterKey   ||
|+--------------+----------------------+---------+----------------+|
||  dev         |  Environmanet name.  |  False  |  EnvName       ||
|+--------------+----------------------+---------+----------------+|
```

### `sync_templates`

Upload CloudFormation templates to S3 bucket.

```bash
$ fab sync_templates
Synchronizing templates local templates to s3://crossroad0201-fabricawscfn/example/dev...
[localhost] local: aws s3 sync templates s3://crossroad0201-fabricawscfn/example/dev --delete --include "*.yaml"
upload: templates\foo.yaml to s3://crossroad0201-fabricawscfn/example/dev/foo.yaml
```

### `create_[StackAlias]`

Create new stack.

You can specify Stack parameter(s) via task parameter (Like this `$ fab create_xxx:Param1=PARAM1,Param2=PARAM2`).

If parameters are not specified by task parameter, prompt will be displayed and input will be prompted.

```bash
$ fab create_bar
Creating stack...
  Stack Name: fabricawscfn-dev-bar
  Template  : https://s3.amazonaws.com/crossroad0201-fabricawscfn/example/dev/subdir/bar.yaml
  Parameters: [{'ParameterValue': 'dev', 'ParameterKey': 'EnvName'}]
Waiting for complete...
Finish.
```

## Optional Tasks

### `profile`, `region` and `account`

Specify AWS profile, region and account.  
If not specified, use AWS credentials default profile.

```bach
$ fab profile:your-profile create_xxxx
$ fab region:us-west-2 create_xxxx
$ fab account:ACCESS_KEY_ID,SECRET_ACCESS_KEY create_xxxx
```

### `params`

Specify Stack parameters bulkly.

```bash
$ fab params:Param1=PARAM1,Param2=PARAM2 create_xxxx create_yyyy
```

### `dryrun`

Turn on DRY-RUN mode, on create / update stack.
DRY-RUN mode is create `Change Set` and show it.

```bash
$ fab dryrun:show_details create_xxxx update_yyyy
```

## One liner

```bash
fab params:Param1=PARAM1,Param2=PARAM2 sync_templates create_xxxx create_yyyy list_stacks list_resources list_exports
```

# Misc

### Using confirmation at task execution

* Enable confirmation using `StackGroup#need_confirm()`.

```Python
StackGroup(...)\
    :
  .need_confirm('Execute task?')
```

* Run with confirmation.

```bash
$ fab update_bar delete_foo
Execute task? [y/N]
```

* Using `force` task to execute task without confirmation.

```bash
$ fab force update_bar delete_foo
```

Usage see [example/fabfile.py](./example/fabfile.py).

# Change log

### 2018/11/15 - Ver.0.1.3

* **\[FIX]** Fix KeyError at `describe_stack` task if detected drift does not exists.

### 2018/11/14 - Ver.0.1.2

* **\[UPDATE]** Supports [drift detection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html) .
  * Added `detect_drift` task.
  * Show detect status on `list_stacks` and `describe_stack` tasks.

### 2018/09/27 - Ver.0.1.1

* **\[UPDATE]** If environment variable [AWS_PROFILE](https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html) is set, use it.

### 2018/09/06 - Ver.0.1.0

* **\[FIX]** Specified Account/Profile/Region are not used on sync_templates task.

### 2017/12/13

* **\[NEW]** Supported confirmation at execute some tasks.(Synchronize templates, Update/Delete stack)

### 2017/12/11

* **\[FIX]** `ls_stacks` does not show all stacks.
* **\[FIX]** `ls_resources` does not show all resources.

### 2017/11/12

* **\[NEW]** Add `profile` task. Specify AWS profile.
* **\[NEW]** Provide task alias.

### 2017/06/28

* **\[NEW]** Add `account` and `region` task. Specify AWS account, region.

### 2017/05/31

* **\[NEW]** Add `dryrun` task.
