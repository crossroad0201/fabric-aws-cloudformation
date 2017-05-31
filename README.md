Fabric task generator for AWS CloudFormation
============================================

A Python library that generates [Fabric](http://www.fabfile.org) tasks to manipulate the stack of AWS CloudFormation.

You will be able to manipulate the CloudFormation stack with the CUI.

```bash
$ fab list_stacks
Stacks:
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
| StackAlias | StackName            |      Status     |           CreatedTime            | UpdatedTime | Description |
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
| foo        | fabricawscfn-dev-foo | CREATE_COMPLETE | 2017-03-05 04:35:12.823000+00:00 |      -      | Foo bucket. |
| bar        | fabricawscfn-dev-bar |   Not created   |                -                 |      -      | -           |
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
```

# Setup

## Requirement

* Python 2.x
* [Fabric](http://www.fabfile.org)
* [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-set-up.html)

## Install

Install `fabricawscfn` (and [Dependencies](./setup.py)) via pip.

```bash
pip install git+https://github.com/crossroad0201/fabric-aws-cloudformation.git
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
  * `templates_local_dir`(OPTIONAL) - Local dir(relative path) where CloudFormation template(s) location.

* `templates_s3_bucket` and `templates_s3_refix` can contains placeholder(Like this `foo-%(environment)s`). Replace by Fabric env.

### 3-2.Define Stack

Define Stack(s) using `StackGroup#define_stack()`.

* Parameters.
  * `alias` - Alias(Short name) of Stack. This name using task parameter.
  * `stack_name` - CloudFormation Stack name.
  * `template_path` - Template file path.(Relative path from `templates_local_dir`)
  * `**kwargs` - Additional arguments for Create/Update/Delete stack. See [Boto3 reference](https://boto3.readthedocs.io/en/latest/reference/services/cloudformation.html#CloudFormation.Client.create_stack).
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

    console            Open AWS Console on your default Web browser.
    create_bar         create stack bar.
    create_foo         create stack foo.
    delete_bar         delete stack bar.
    delete_foo         delete stack foo.
    desc_stack         Describe existing stack.
    env_on             Set environment.(Default dev)
    list_exports       List exports.
    list_resources     List existing stack resources.
    list_stacks        List stacks.
    params             Set parameters. (Applies to all tasks)
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
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
| StackAlias | StackName            |      Status     |           CreatedTime            | UpdatedTime | Description |
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
| foo        | fabricawscfn-dev-foo | CREATE_COMPLETE | 2017-03-05 04:35:12.823000+00:00 |      -      | Foo bucket. |
| bar        | fabricawscfn-dev-bar |   Not created   |                -                 |      -      | -           |
+------------+----------------------+-----------------+----------------------------------+-------------+-------------+
```

### `desc_stack:[StackAlias or StackName]`

Show stack detail.

```bash
$ fab desc_stack:foo
Stack:
+----------------------+-----------------+----------------------------------+-------------+-------------+
| StackName            |      Status     |           CreatedTime            | UpdatedTime | Description |
+----------------------+-----------------+----------------------------------+-------------+-------------+
| fabricawscfn-dev-foo | CREATE_COMPLETE | 2017-03-05 04:35:12.823000+00:00 |     None    | Foo bucket. |
+----------------------+-----------------+----------------------------------+-------------+-------------+
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
| 2017-03-05 04:35:55.694000+00:00 |  CREATE_COMPLETE   | AWS::CloudFormation::Stack | fabricawscfn-dev-foo | None                        |
| 2017-03-05 04:35:53.009000+00:00 |  CREATE_COMPLETE   | AWS::S3::Bucket            | Bucket               | None                        |
| 2017-03-05 04:35:32.308000+00:00 | CREATE_IN_PROGRESS | AWS::S3::Bucket            | Bucket               | Resource creation Initiated |
| 2017-03-05 04:35:31.102000+00:00 | CREATE_IN_PROGRESS | AWS::S3::Bucket            | Bucket               | None                        |
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
