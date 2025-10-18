# !/usr/bin/env python
# -*- encoding: utf-8 -*-
import io

from setuptools import setup

import pass_cli

with open('requirements.txt', 'r') as fh:
    dependencies = [l.strip() for l in fh]

setup(name='pass_cli',
      version=pass_cli.__version__,
      description='CLI interface for pass',
      keywords='pass_cli',
      author='Aleksandr Block',
      author_email='aleksandr.block@gmail.com',
      url='https://github.com/a7f4/pass_cli',
      license='MIT',
      long_description=io.open('./README.md', 'r', encoding='utf-8').read(),
      long_description_content_type="text/markdown",
      platforms='any',
      zip_safe=False,
      include_package_data=True,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
          "License :: OSI Approved :: MIT License",
          "Operating System :: Unix"
      ],
      packages=['pass_cli'],
      install_requires=dependencies,
      extras_require={
          ':python_version == "3.5"': ['configparser']
      },
      entry_points={
          'console_scripts': [
              'pass_cli = pass_cli.__main__:main',
          ]
      })
