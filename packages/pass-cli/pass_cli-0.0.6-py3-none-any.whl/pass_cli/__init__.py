# -*- encoding: utf-8 -*-

"""
CLI interface for pass.

:Copyright: © 2025, Aleksandr Block.
:License: MIT (see /LICENSE).
"""

import configparser
import os

import pkg_resources

APP_NAME = 'pass_cli'

__title__ = APP_NAME
__version__ = '0.0.6'
__author__ = 'Aleksandr Block'
__license__ = 'MIT'
__docformat__ = 'restructuredtext en'

__all__ = ('config',)

# Config directory setup
conf_home = os.getenv('XDG_CONFIG_HOME')
if conf_home is None:
    conf_home = os.path.expanduser('~/.config/')

conf_dir = os.path.join(conf_home, APP_NAME)
conf_name = f'{APP_NAME}.ini'
conf_path = os.path.join(conf_dir, conf_name)

if not os.path.exists(conf_home):
    os.mkdir(conf_home)
if not os.path.exists(conf_dir):
    os.mkdir(conf_dir)

conf_skel = f'{APP_NAME}', f'data/{conf_name}.skel'
if not os.path.exists(conf_path):
    print(f"{conf_name} does not exist, creating")
    with open(conf_path, 'wb') as fh:
        fh.write(pkg_resources.resource_string(*conf_skel))
    print("created " + conf_path)

# Configuration file support
config = configparser.ConfigParser()
config.read_string(pkg_resources.resource_string(*conf_skel).decode('utf-8'))
config.read([conf_path], encoding='utf-8')
