# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['src']

package_data = \
{'': ['*']}

install_requires = \
['fortitudo-tech>=1.1.8,<2.0.0',
 'jupyterlab>=4.3.0,<5.0.0',
 'seaborn>=0.13.0,<0.14.0',
 'yfinance>=0.2.50,<0.3.0']

setup_kwargs = {
    'name': 'pcrm-book',
    'version': '1.0.4',
    'description': 'Accompanying Python code to the Portfolio Construction and Risk Management book by Anton Vorobets.',
    'long_description': "[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fortitudo-tech/pcrm-book/HEAD?urlpath=%2Fdoc%2Ftree%2F%2Fcode)\n\n# Portfolio Construction and Risk Management book's Python code\nThis repository contains the accompanying code to Portfolio Construction and Risk\nManagement book © 2025 by Anton Vorobets.\n\n[You can find the latest PDF version of the book in this Substack post](https://antonvorobets.substack.com/p/pcrm-book).\n\nFor a quick video introduction to what you can expect from this book and some\nfundamental perspectives, [watch this video](https://antonvorobets.substack.com/p/anton-vorobets-next-generation-investment-framework).\n\nSubscribe to the [Quantamental Investing Substack publication](https://antonvorobets.substack.com)\nto stay updated on all news related to the book.\n\nYou can still support the project through [buy me a coffee](https://buymeacoffee.com/antonvorobets)\nor [Substack](https://antonvorobets.substack.com).\n\n# Applied Quantitative Investment Management course\nYou can access [a course that carefully goes through the book and its accompanying\ncode](https://antonvorobets.substack.com/t/course) from this repository.\n\n[Read more about the course and how you get access here](https://antonvorobets.substack.com/p/course-q-and-a).\n\n# Running the code\nIt is recommended to install the book's code dependencies in a \n[conda environment](https://conda.io/projects/conda/en/latest/user-guide/concepts/environments.html).\n\nAfter cloning the repository to your local machine, you can install the dependencies\nusing the following command in your terminal:\n\n    conda env create -f environment.yml\n\nYou can then activate the conda environment and start a [JupyterLab](https://jupyter.org/)\ninstance using the following commands:\n\n    conda activate pcrm-book\n    jupyter lab\n\nIf you are completely new to [conda environments](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)\nand Jupyter notebooks, you can find a lot of information online.\n\nYou can also run the code without any local installations using [Binder](https://mybinder.org/v2/gh/fortitudo-tech/pcrm-book/HEAD?urlpath=%2Fdoc%2Ftree%2F%2Fcode).\nNote however that Binder servers are not always available and might have\ninsufficient resources to run all the examples.\n\n# Feedback\nPlease post your feedback in the community Discussions forum. I will try to\nincorporate the feedback in the book. See the book's preface for some general\nperspectives on what it tries to achieve, and which kind feedback will\nbe considered appropriate.\n\n# Thank you for your support\nYour support made it possible for this book to be written.\n\nBesides your personal monetary support, you can help improve the quality of the\nbook by simply publicly sharing your positive experience with the book and its code,\nthereby encouraging more people to support the project. You\nare also encouraged to give this and the supporting\n[fortitudo.tech](https://github.com/fortitudo-tech/fortitudo.tech)\nrepository a star.\n\nNo matter how much economic support this project realistically gets, it will only\nbe a small fraction of the opportunity costs from writing the book and making it\nfreely available online. Hence, you are encouraged to support it by the amount that\nyou think it is worth to you.\n\n[If you claim one of the significiant contributor perks](https://igg.me/at/pcrm-book),\nyou can choose to be recognized in the book's preface. You will additionally get a one-year\npaid complimentary Substack subscription to the [Quantamental Investing publication](https://antonvorobets.substack.com),\nwhich contains exclusive case studies and allow you to continue asking questions.\n\n# Licenses\nThe Portfolio Construction and Risk Management book © 2025 by Anton Vorobets is licensed\nunder Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International. To view\na copy of this license, visit https://creativecommons.org/licenses/by-nc-nd/4.0/\n\nThe accompanying code to the Portfolio Construction and Risk Management book © 2025 by\nAnton Vorobets is licensed under version 3 of the GNU General Public License. To view\na copy of this license, visit https://www.gnu.org/licenses/gpl-3.0.en.html\n",
    'author': 'Anton Vorobets',
    'author_email': 'admin@fortitudo.tech',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://pcrmbook.com',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<3.14',
}


setup(**setup_kwargs)
