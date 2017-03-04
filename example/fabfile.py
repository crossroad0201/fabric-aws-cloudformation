# -*- coding: utf-8 -*-
from __future__ import print_function

from fabric.api import *

## Import from local dir.
# import sys
# sys.path.append('../fabricawscfn')

from fabricawscfn import *

env.env_name = 'dev'

StackGroup(globals(), 'crossroad0201-fabricawscfn', 'example/%(env_name)s', 'templates')\
  .define_stack('foo', 'fabricawscfn-%(env_name)s-foo', 'foo.yaml')\
  .define_stack('bar', 'fabricawscfn-%(env_name)s-bar', 'subdir/bar.yaml')

@task
def env_on(env_name):
  env.env_name = env_name
