#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
  name             = 'fabricawscfn',
  version          = '0.0.1',
  description      = 'Fabric task generator for AWS CloudFormation.',
  license          = 'MIT',
  author           = 'Yohei TSUJI',
  url              = 'https://github.com/crossroad0201/fabric-awscfn',
  packages         = find_packages(),
  install_requires = [
    'fabric',
    'boto3',
    'prettytable'
  ]
)