# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['cloudsh', 'cloudsh.commands']

package_data = \
{'': ['*'], 'cloudsh': ['args/*']}

install_requires = \
['argcomplete>=3.5.3,<4.0.0',
 'argx>=0.3,<0.4',
 'python-dateutil>=2.9.0.post0,<3.0.0',
 'python-simpleconf[toml]>=0.7,<0.8',
 'yunpath>=0.1,<0.2']

extras_require = \
{'all': ['azure-storage-blob>=12,<13',
         'azure-storage-file-datalake>=12,<13',
         'boto3>=1.34,<2.0',
         'google-cloud-storage>=3.0,<4.0'],
 'aws': ['boto3>=1.34,<2.0'],
 'azure': ['azure-storage-blob>=12,<13', 'azure-storage-file-datalake>=12,<13'],
 'gcs': ['google-cloud-storage>=3.0,<4.0'],
 'gs': ['google-cloud-storage>=3.0,<4.0']}

entry_points = \
{'console_scripts': ['cloudsh = cloudsh.main:main']}

setup_kwargs = {
    'name': 'cloudsh',
    'version': '0.1.5',
    'description': 'A Python CLI wrapping common Linux commands for local/cloud files.',
    'long_description': 'None',
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
