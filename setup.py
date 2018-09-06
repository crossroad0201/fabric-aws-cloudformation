#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
  name             = 'fabricawscfn',
  version          = '0.1.0',
  description      = 'Fabric task generator for AWS CloudFormation.',
  license          = 'MIT',
  author           = 'Yohei TSUJI',
  url              = 'https://github.com/crossroad0201/fabric-awscfn',
  keywords         = 'fabric aws cloudformation',
  packages         = find_packages(),
  install_requires = [
    'fabric<2.0',
    'boto3',
    'prettytable'
  ]
)
