# Copyright: (c) 2024, Dell Technologies

"""Setup file for PowerStore SDK"""

from setuptools import setup


setup(name='mv-pypowerstore',
      version='3.4.1.1',
      description='Python Library for Dell PowerStore Modified by Moviri for use with Dynatrace extensions.',
      author='Moviri',
      author_email='dynatrace_extensions@moviri.com',
      install_requires=[
        'urllib3>=1.26.7',
        'requests>=2.23.0'
      ],
      license_files = ('LICENSE',),
      classifiers=['License :: OSI Approved :: Apache Software License'],
      url='https://github.com/dell/python-powerstore',
      packages=['PyPowerStore', 'PyPowerStore.utils', 'PyPowerStore.objects'],
      )
