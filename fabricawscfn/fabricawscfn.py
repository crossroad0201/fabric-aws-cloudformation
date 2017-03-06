# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import OrderedDict
from sets import Set

import boto3
import botocore
from prettytable import PrettyTable
from fabric.api import *
from fabric.operations import *
from fabric.utils import *
from fabric.colors import green, blue, yellow, red

class StackGroup(object):
  def __init__(self, templates_s3_bucket, templates_s3_prefix, templates_local_dir = '.'):
    '''
    Create StackGroup.

    :param templates_s3_bucket: S3 bucket name for templates. (allow placeholder. will be replace by env.)
    :param templates_s3_prefix: S3 prefix(folder) for templates. (allow placeholder. will be replace by env.)
    :param templates_local_dir: Local dir for templates.(OPTIONAL. Default current dir)
    '''
    # {Stack Alias, StackDef}
    self.stack_defs = OrderedDict()
    self.templates_s3_bucket = templates_s3_bucket
    self.templates_s3_prefix = templates_s3_prefix
    self.templates_local_dir = templates_local_dir

    # Init boto3 clients.
    self.cfn_client = boto3.client('cloudformation')
    self.cfn_resource = boto3.resource('cloudformation')

  def __add_fabric_task(self, namespace, task_name, task_method):
    wrapper = task(name = task_name)
    rand = '%d' % (time.time() * 100000)
    namespace['task_%s_%s' % (task_name, rand)] = wrapper(task_method)

  def __colord_status(self, status):
    if status.endswith('_COMPLETE'):
      return green(status)
    if status.endswith('_IN_PROGRESS'):
      return yellow(status)
    if status.endswith('_FAILED'):
      return red(status)
    else:
      return status

  def __format_datetime(self, datetime):
    return '{0:%Y-%m-%d %H:%M:%S %Z}'.format(datetime) if datetime is not None else '-'

  def __shorten(self, str, slen, elen):
    if len(str) <= (slen + elen):
      return str
    else:
      if slen < 1:
        return '..%s' % str[len(str) - elen + 2:len(str)]
      elif elen < 1:
        return '%s..' % str[0:slen - 2]
      else:
        return '%s..%s' % (str[0:slen -1], str[len(str) - elen + 1:len(str)])

  def actual_templates_s3_bucket(self):
    return self.templates_s3_bucket % env

  def actual_templates_s3_prefix(self):
    return self.templates_s3_prefix % env

  def define_stack(self, alias, stack_name, template_path, **kwargs):
    '''
    Define stack.

    :param alias: Stack alias.
    :param stack_name: Stack name.(allow placeholder. will be replace by env.)
    :param template_path: Template file relative path.
    :param kwargs: Optional stack arguments.
    :return: self
    '''
    stack_def = StackDef(self, alias, stack_name, template_path, **kwargs)
    self.stack_defs[alias] = stack_def

    return self

  def generate_task(self, namespace):
    '''
    Generate Fabric task for defined Stack(s).

    :param namespace: Task add to.
    :return: self
    '''
    # Add general tasks.
    self.__add_fabric_task(namespace, 'params', self.params)
    self.__add_fabric_task(namespace, 'validate_template', self.validate_template)
    self.__add_fabric_task(namespace, 'sync_templates', self.sync_templates)
    self.__add_fabric_task(namespace, 'ls_stacks', self.ls_stacks)
    self.__add_fabric_task(namespace, 'desc_stack', self.desc_stack)
    self.__add_fabric_task(namespace, 'ls_resources', self.ls_resources)
    self.__add_fabric_task(namespace, 'ls_exports', self.ls_exports)

    # Add stack tasks.
    for stack_def in self.stack_defs.values():
      for operation in stack_def.get_stack_operations():
        operation_name = operation.__name__
        operation.__func__.__doc__ = '%s stack %s.' % (operation_name, stack_def.stack_alias)
        task_name = '%s_%s' % (operation_name, stack_def.stack_alias)
        self.__add_fabric_task(namespace, task_name, operation)

    return self

  def params(self, **kwparams):
    '''
    Set parameters. (Applies to all tasks)

    :param kwparams: parameters.
    '''
    for param_name, param_value in kwparams.iteritems():
      env[param_name] = param_value

  def validate_template(self, alias):
    '''
    Validate template on local dir.

    :param alias: Stack alias.
    '''
    template_local_path = '%s/%s' % (
      self.templates_local_dir,
      self.stack_defs[alias].template_path
    )
    print('Validating template %s...' % template_local_path)
    local(
      "aws cloudformation validate-template --template-body file://%s --output table" % template_local_path
    )

  def sync_templates(self):
    '''
    Synchronize templates local dir to S3 bucket.
    '''
    s3url = 's3://%s/%s' % (self.actual_templates_s3_bucket(), self.actual_templates_s3_prefix())
    print('Synchronizing templates local %s to %s...' % (self.templates_local_dir, s3url))
    local('aws s3 sync %s %s --delete --include \"*.yaml\"' % (self.templates_local_dir, s3url))

  def ls_stacks(self):
    '''
    List stacks.
    '''
    paginator = self.cfn_client.get_paginator('list_stacks')
    pages = paginator.paginate(
      StackStatusFilter = [
        'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE',
        'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE',
        'DELETE_IN_PROGRESS', 'DELETE_FAILED', # 'DELETE_COMPLETE',
        'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE',
        'REVIEW_IN_PROGRESS'],
      PaginationConfig = {
        'MaxItems': 500
      }
    )

    # TODO Refactoring.
    defined_stack_names = Set()
    defined_stack_aliases = {}
    for stack_def in self.stack_defs.values():
      defined_stack_names.add(stack_def.actual_stack_name())
      defined_stack_aliases[stack_def.actual_stack_name()] = stack_def.stack_alias

    def is_in_stack_group(stack_name):
      for defined_stack_name in defined_stack_names:
        # startswith(...-) for Chained stack.
        if stack_name == defined_stack_name or stack_name.startswith(defined_stack_name + '-'):
          return True
      return False

    table = PrettyTable(['StackAlias', 'StackName', 'Status', 'CreatedTime', 'UpdatedTime', 'Description'])
    table.align['StackAlias'] = 'l'
    table.align['StackName'] = 'l'
    table.align['Description'] = 'l'
    table.padding_width = 1
    # Append existing stacks.
    for page in pages:
      summaries = page['StackSummaries']
      for summary in summaries:
        stack_name = summary['StackName']
        if is_in_stack_group(stack_name):
          table.add_row([
            # TODO Show Alias at chaining stack.
            defined_stack_aliases.pop(stack_name) if defined_stack_aliases.has_key(stack_name) else '', # pop!
            self.__shorten(stack_name, 40, 5),
            self.__colord_status(summary['StackStatus']),
            self.__format_datetime(summary['CreationTime']),
            self.__format_datetime(summary['LastUpdatedTime']) if summary.has_key('LastUpdatedTime') else '-',
            self.__shorten(summary['TemplateDescription'], 70, 0)
          ])
    # Append stacks that have not been created yet.
    for not_exist_stack_name, not_exist_stack_alias in defined_stack_aliases.items():
      table.add_row([
        not_exist_stack_alias,
        not_exist_stack_name,
        'Not created',
        '-',
        '-',
        '-'
      ])

    print(blue('Stacks:', bold = True))
    print(table)

  def desc_stack(self, alias):
    '''
    Describe existing stack.

    :param alias: Stack alias.
    '''
    stack = self.cfn_resource.Stack(self.stack_defs[alias].actual_stack_name())
    try:
      stack.stack_id
    except botocore.exceptions.ClientError:
      # Stack does not exists
      print(yellow('Stack %s does not exists.' % stack.name))
      return


    print(blue('Stack:', bold = True))
    table = PrettyTable()
    table.add_column('StackName', [stack.stack_name])
    table.align['StackName'] = 'l'
    table.add_column('Status', [self.__colord_status(stack.stack_status)])
    table.add_column('CreatedTime', [self.__format_datetime(stack.creation_time)])
    table.add_column('UpdatedTime', [self.__format_datetime(stack.last_updated_time)])
    table.add_column('Description', [self.__shorten(stack.description, 70, 0)])
    print(table)

    print(blue('Parameters:', bold = True))
    if stack.parameters is None:
      print('No parameters.')
    else:
      table = PrettyTable(['Key', 'Value'])
      table.align['Key'] = 'l'
      table.align['Value'] = 'l'
      for param in stack.parameters:
        table.add_row([
          param['ParameterKey'],
          param['ParameterValue']
        ])
      print(table)

    print(blue('Outputs:', bold = True))
    if stack.outputs is None:
      print('No outputs.')
    else:
      table = PrettyTable(['Key', 'Value', 'Description'])
      table.align['Key'] = 'l'
      table.align['Value'] = 'l'
      table.align['Description'] = 'l'
      for output in stack.outputs:
        table.add_row([
          output['OutputKey'],
          output['OutputValue'],
          self.__shorten(output['Description'], 70, 0) if output.has_key('Description') else '-'
        ])
      print(table)

    print(blue('Events(last 20):', bold = True))
    table = PrettyTable(['Timestamp', 'Status', 'Type', 'LogicalID', 'StatusReason'])
    table.align['Timestamp'] = 'l'
    table.align['Type'] = 'l'
    table.align['LogicalID'] = 'l'
    table.align['StatusReason'] = 'l'
    # Show latest 20 events.
    for event in list(stack.events.all())[:20]:
      table.add_row([
        self.__format_datetime(event.timestamp),
        self.__colord_status(event.resource_status),
        event.resource_type,
        event.logical_resource_id,
        event.resource_status_reason
      ])
    print(table)

  # TODO Bulk create all stacks.
  # TODO Bulk update all stacks.
  # TODO Bulk delete all stacks.

  def ls_resources(self):
    '''
    List existing stack resources.
    '''
    paginator = self.cfn_client.get_paginator('list_stack_resources')

    table = PrettyTable(['StackName', 'LogicalID', 'PhysicalID', 'Type', 'Status', 'UpdatedTime'])
    table.align['StackName'] = 'l'
    table.align['LogicalID'] = 'l'
    table.align['PhysicalID'] = 'l'
    table.align['Type'] = 'l'

    for stack_def in self.stack_defs.values():
      stack_name = stack_def.actual_stack_name()
      try:
        pages = paginator.paginate(
          StackName = stack_name,
          PaginationConfig = {
            'MaxItems': 100
          }
        )
        for page in pages:
          summaries = page['StackResourceSummaries']
          for summary in summaries:
            table.add_row([
              stack_name,
              summary['LogicalResourceId'],
              self.__shorten(summary['PhysicalResourceId'], 40, 5),
              summary['ResourceType'],
              self.__colord_status(summary['ResourceStatus']),
              self.__format_datetime(summary['LastUpdatedTimestamp'])
            ])
      except botocore.exceptions.ClientError:
        # Ignore this stack if exception occurred.
        pass

    print(blue('Resrouces:', bold = True))
    print(table)

  def ls_exports(self):
    '''
    List exports.
    '''
    def get_exported_stack_name(export):
      exportingStackId = export['ExportingStackId']
      for stack_def in self.stack_defs.values():
        stack_name = stack_def.actual_stack_name()
        if stack_name in exportingStackId: # Contains stack name in exporting stack name.
          return stack_name
      return None

    exports = self.cfn_client.list_exports()

    table = PrettyTable(['ExportedStackName', 'ExportName', 'ExportValue'])
    table.align['ExportedStackName'] = 'l'
    table.align['ExportName'] = 'l'
    table.align['ExportValue'] = 'l'
    for export in exports['Exports']:
      exported_stack_name = get_exported_stack_name(export)
      if exported_stack_name is not None:
        table.add_row([
          exported_stack_name,
          export['Name'],
          export['Value']
        ])
    print(blue('Exports:', bold = True))
    print(table)


class StackDef(object):
  def __init__(self, stack_group, stack_alias, stack_name, template_path, **kwargs):
    self.stack_group = stack_group
    self.stack_alias = stack_alias
    self.stack_name = stack_name
    self.template_path = template_path
    self.kwargs = kwargs

  def actual_stack_name(self):
    return self.stack_name % env

  def template_s3_url(self):
    return 'https://s3.amazonaws.com/%s/%s/%s' % (
      self.stack_group.actual_templates_s3_bucket(),
      self.stack_group.actual_templates_s3_prefix(),
      self.template_path
    )

  def create(self, **kwparams):
    # Override Fabric env with task parameter.
    self.stack_group.params(**kwparams)

    # Get template definition.
    template = self.stack_group.cfn_client.get_template_summary(
      TemplateURL = self.template_s3_url()
    )

    # Resolve parameters from task parameter, fabric env, prompt.
    params = []
    for param_def in template['Parameters']:
      param_key = param_def['ParameterKey']
      if env.has_key(param_key):
        # Use specified parameter.
        param_value = env[param_key]
      else:
        if param_def.has_key('DefaultValue'):
          default_value = param_def['DefaultValue']
          if param_def.has_key('Description'):
            # Prompt parameter with description, default value.
            param_value = prompt('%s? - %s' % (param_key, param_def['Description']), default = default_value)
          else:
            # Prompt parameter with default value.
            param_value = prompt('%s?' % param_key, default = default_value)
        else:
          if param_def.has_key('Description'):
            # Prompt parameter with description.
            param_value = prompt('%s? - %s' % (param_key, param_def['Description']))
          else:
            # Prompt parameter.
            param_value = prompt('%s?' % param_key)

        if not param_value:
          raise Exception('Missing require parameter %s.' % (param_key))

      params.append({
        'ParameterKey': param_key,
        'ParameterValue': param_value
      })

    # TODO Async execution.
    # Create stack.
    print('Creating stack...')
    print('  Stack Name: %s' % self.actual_stack_name())
    print('  Template  : %s' % self.template_s3_url())
    print('  Parameters: %s' % params)
    self.stack_group.cfn_resource.create_stack(
      StackName = self.actual_stack_name(),
      TemplateURL = self.template_s3_url(),
      Parameters = params,
      **self.kwargs
    )

    # Wait create complete.
    print('Waiting for complete...')
    self.stack_group.cfn_client.get_waiter('stack_create_complete').wait(
      StackName = self.actual_stack_name()
    )
    print('Finish.')

  def update(self, **kwparams):
    # Override Fabric env with task parameter.
    self.stack_group.params(**kwparams)

    # Get exists stack.
    stack = self.stack_group.cfn_resource.Stack(self.actual_stack_name())
    def get_previous_param_value(param_key):
      for param in stack.parameters:
        if param['ParameterKey'] == param_key:
          return param['ParameterValue']
      return None

    # Get template definition.
    template = self.stack_group.cfn_client.get_template_summary(
      TemplateURL = self.template_s3_url()
    )

    # Resolve parameters from task parameter, fabric env, prompt.
    params = []
    for param_def in template['Parameters']:
      param_key = param_def['ParameterKey']
      if env.has_key(param_key):
        # Use specified parameter.
        param_value = env[param_key]
      else:
        prev_value = get_previous_param_value(param_key)
        if prev_value is not None:
          if param_def.has_key('Description'):
            # Prompt parameter with description, previous value.
            param_value = prompt('%s? - %s' % (param_key, param_def['Description']), default = prev_value)
          else:
            # Prompt parameter with previous value.
            param_value = prompt('%s?' % param_key, default = prev_value)
        elif param_def.has_key('DefaultValue'):
          default_value = param_def['DefaultValue']
          if param_def.has_key('Description'):
            # Prompt parameter with description, default value.
            param_value = prompt('%s? - %s' % (param_key, param_def['Description']), default = default_value)
          else:
            # Prompt parameter with default value.
            param_value = prompt('%s?' % param_key, default = default_value)
        else:
          if param_def.has_key('Description'):
            # Prompt parameter with description.
            param_value = prompt('%s? - %s' % (param_key, param_def['Description']))
          else:
            # Prompt parameter.
            param_value = prompt('%s?' % param_key)

      params.append({
        'ParameterKey': param_key,
        'ParameterValue': param_value
      })

    # TODO Confirm update.
    # TODO Async execution.
    # Update stack.
    print('Updating stack...')
    print('  Stack Name: %s' % self.actual_stack_name())
    print('  Template  : %s' % self.template_s3_url())
    print('  Parameters: %s' % params)
    try:
      stack.update(
        TemplateURL = self.template_s3_url(),
        Parameters = params,
        **self.kwargs
      )
    except botocore.exceptions.ClientError as e:
      if 'No updates are to be performed' in e.args[0]:
        print(yellow('No changes.'))
      else:
        raise e
    else:
      # Wait update complete.
      print('Waiting for complete...')
      self.stack_group.cfn_client.get_waiter('stack_update_complete').wait(
        StackName = self.actual_stack_name()
      )
      print('Finish.')

  def delete(self):
    # TODO Async execution.
    # Delete stack.
    print('Deleting stack...')
    print('  Stack Name: %s' % self.actual_stack_name())
    self.stack_group.cfn_resource.Stack(self.actual_stack_name()).delete()

    # Wait delete complete.
    print('Waiting for complete...')
    self.stack_group.cfn_client.get_waiter('stack_delete_complete').wait(
      StackName = self.actual_stack_name()
    )
    print('Finish.')

  def get_stack_operations(self):
    return [self.create, self.update, self.delete]
