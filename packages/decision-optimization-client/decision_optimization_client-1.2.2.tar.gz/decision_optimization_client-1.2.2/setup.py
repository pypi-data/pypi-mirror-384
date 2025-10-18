# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2018
# --------------------------------------------------------------------------
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


required = ['requests', 'six']

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    try:
        with open(os.path.join(HERE, *parts)) as f:
            return f.read()
    except:
        return None

setup(name='decision_optimization_client',
      version='1.2.2', # Check version number on either test pypi or official pypi (depending on where you want to push this)
      description='The IBM Decision Optimization Scenario Python client',
      author='The IBM Decision Optimization on team',
      packages=['decision_optimization_client'],
      include_package_data=True,
      install_requires=required,
      license=read('LICENSE.txt')
      )
