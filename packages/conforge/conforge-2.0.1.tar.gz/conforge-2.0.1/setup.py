# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['conforge']

package_data = \
{'': ['*']}

install_requires = \
['jinja2>=3.1.6,<4.0.0', 'pyyaml>=6.0.3,<7.0.0']

entry_points = \
{'console_scripts': ['conforge = conforge.cli:run_app']}

setup_kwargs = {
    'name': 'conforge',
    'version': '2.0.1',
    'description': 'A tool for generating config files from given templates and variables.',
    'long_description': '# Conforge\n\nA tool for generating config files from given templates and variables.\n\n## Installation & Usage\n\nConforge is available in the Python Package Index (PyPI) and you can use the below command to install it using `pipx`.\n\n```shell\n$ pipx install conforge\n```\n\nRun Conforge using the below command.\n\n```shell\n$ conforge -t yaml conforge.yml\n```\n\nYou can also run Conforge using Docker. Refer to the [wiki page](https://codeberg.org/scripthoodie/conforge/wiki/Installation#installation-usage) for detailed instructions on installation and usage.\n\n## License\n\nConforge is licensed under the terms of GPL version 3.0. See the [LICENSE](https://codeberg.org/scripthoodie/conforge/src/branch/main/LICENSE) file for details.',
    'author': 'ScriptHoodie',
    'author_email': 'dev@scripthoodie.dev',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.11,<4.0',
}


setup(**setup_kwargs)
