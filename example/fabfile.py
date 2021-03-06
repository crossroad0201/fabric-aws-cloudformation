# -*- coding: utf-8 -*-
"""
Example fabfile.py using fabricawscfn.
"""
from __future__ import print_function

from fabric.api import *

## Import from local dir.
# import sys
# sys.path.append('../fabricawscfn')

from fabricawscfn import *

env.EnvName = 'dev'
@task
def env_on(env_name):
    """
    Set environment.(Default dev)

    :param env_name: Environment name.
    """
    env.EnvName = env_name
    # Enable confirmation if environment is production.
    if env_name == 'production':
        stack_group.need_confirm('Execute task on production?')

# Change to your S3 bucket.
stack_group = StackGroup('crossroad0201-fabricawscfn', 'example/%(EnvName)s', 'templates')\
    .define_stack('foo', 'fabricawscfn-%(EnvName)s-foo', 'foo.yaml')\
    .define_stack('bar', 'fabricawscfn-%(EnvName)s-bar', 'subdir/bar.yaml', Tags=[{'Key':'example', 'Value':'EXAMPLE'}])\
    .generate_task(globals())
