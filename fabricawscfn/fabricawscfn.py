# -*- coding: utf-8 -*-
from __future__ import print_function

import boto3
import botocore
from prettytable import PrettyTable
from fabric.api import *
from fabric.operations import *
from fabric.utils import *
from fabric.colors import green, blue, yellow, red

class StackGroup(object):
  def __init__(self, namespace, templates_s3_bucket, templates_s3_prefix, templates_local_dir = '.'):
    self.namespace = namespace
    self.templates_s3_bucket = templates_s3_bucket
    self.templates_s3_prefix = templates_s3_prefix
    self.templates_local_dir = templates_local_dir

    self.__add_fabric_task('sync_templates', self.sync_templates)
    self.__add_fabric_task('ls_stacks', self.ls_stacks)

  def __add_fabric_task(self, task_name, task_method):
    wrapper = task(name = task_name)
    rand = '%d' % (time.time() * 100000)
    self.namespace['task_%s_%s' % (task_name, rand)] = wrapper(task_method)

  def actual_templates_s3_bucket(self):
    return self.templates_s3_bucket % env

  def actual_templates_s3_prefix(self):
    return self.templates_s3_prefix % env

  def sync_templates(self):
    s3url = 's3://%s/%s' % (self.actual_templates_s3_bucket(), self.actual_templates_s3_prefix())
    local('aws s3 sync %s %s --delete --include \"*.yaml\"' % (self.templates_local_dir, s3url))

  def ls_stacks(self):
    print('ls_stacks')

  def define_stack(self, name, stack_name, template_path):
    stack_def = StackDef(self, stack_name, template_path)

    for operation in stack_def.get_operations():
      operation_name = operation.__name__
      operation.__func__.__doc__ = '%s %s.' % (operation_name, stack_def.stack_name)
      task_name = '%s_%s' % (operation_name, name)
      self.__add_fabric_task(task_name, operation)

    return self

class StackDef(object):
  def __init__(self, stack_group, stack_name, template_path):
    self.stack_group = stack_group
    self.stack_name = stack_name
    self.template_s3_url = 'https://s3.amazonaws.com/%s/%s/%s' % (
      stack_group.actual_templates_s3_bucket(),
      stack_group.actual_templates_s3_prefix(),
      template_path
    )

  def actual_stack_name(self):
    return self.stack_name % env

  def create(self):
    boto3.resource('cloudformation').create_stack(
      StackName = self.actual_stack_name(),
      TemplateURL = self.template_s3_url,
      Parameters = [{'ParameterKey': 'EnvName', 'ParameterValue': 'test'}]
    )

    boto3.client('cloudformation').get_waiter('stack_create_complete').wait(
      StackName = self.actual_stack_name()
    )

  def delete(self):
    boto3.resource('cloudformation').Stack(self.actual_stack_name()).delete()

    boto3.client('cloudformation').get_waiter('stack_delete_complete').wait(
      StackName = self.actual_stack_name()
    )

  def get_operations(self):
    return [self.create, self.delete]
