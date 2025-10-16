# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['datar', 'datar.apis', 'datar.core', 'datar.data']

package_data = \
{'': ['*']}

install_requires = \
['pipda>=0.13.1,<0.14.0',
 'python-simpleconf[toml]>=0.7,<0.8',
 'simplug>=0.5,<0.6']

extras_require = \
{'arrow': ['datar-arrow>=0.1,<0.2'],
 'numpy': ['datar-numpy>=0.3.4,<0.4.0'],
 'pandas': ['datar-pandas>=0.5.6,<0.6.0']}

setup_kwargs = {
    'name': 'datar',
    'version': '0.15.11',
    'description': 'A Grammar of Data Manipulation in python',
    'long_description': '# datar\n\nA Grammar of Data Manipulation in python\n\n<!-- badges -->\n[![Pypi][6]][7] [![Github][8]][9] ![Building][10] [![Docs and API][11]][5] [![Codacy][12]][13] [![Codacy coverage][14]][13] [![Downloads][20]][7]\n\n[Documentation][5] | [Reference Maps][15] | [Notebook Examples][16] | [API][17]\n\n`datar` is a re-imagining of APIs for data manipulation in python with multiple backends supported. Those APIs are aligned with tidyverse packages in R as much as possible.\n\n## Installation\n\n```shell\npip install -U datar\n\n# install with a backend\npip install -U datar[pandas]\n\n# More backends support coming soon\n```\n\n<!-- ## Maximum compatibility with R packages\n\n|Package|Version|\n|-|-|\n|[dplyr][21]|1.0.8| -->\n\n## Backends\n\n|Repo|Badges|\n|-|-|\n|[datar-numpy][1]|![3] ![18]|\n|[datar-pandas][2]|![4] ![19]|\n|[datar-arrow][22]|![23] ![24]|\n\n## Example usage\n\n```python\n# with pandas backend\nfrom datar import f\nfrom datar.dplyr import mutate, filter_, if_else\nfrom datar.tibble import tibble\n# or\n# from datar.all import f, mutate, filter_, if_else, tibble\n\ndf = tibble(\n    x=range(4),  # or c[:4]  (from datar.base import c)\n    y=[\'zero\', \'one\', \'two\', \'three\']\n)\ndf >> mutate(z=f.x)\n"""# output\n        x        y       z\n  <int64> <object> <int64>\n0       0     zero       0\n1       1      one       1\n2       2      two       2\n3       3    three       3\n"""\n\ndf >> mutate(z=if_else(f.x>1, 1, 0))\n"""# output:\n        x        y       z\n  <int64> <object> <int64>\n0       0     zero       0\n1       1      one       0\n2       2      two       1\n3       3    three       1\n"""\n\ndf >> filter_(f.x>1)\n"""# output:\n        x        y\n  <int64> <object>\n0       2      two\n1       3    three\n"""\n\ndf >> mutate(z=if_else(f.x>1, 1, 0)) >> filter_(f.z==1)\n"""# output:\n        x        y       z\n  <int64> <object> <int64>\n0       2      two       1\n1       3    three       1\n"""\n```\n\n```python\n# works with plotnine\n# example grabbed from https://github.com/has2k1/plydata\nimport numpy\nfrom datar import f\nfrom datar.base import sin, pi\nfrom datar.tibble import tibble\nfrom datar.dplyr import mutate, if_else\nfrom plotnine import ggplot, aes, geom_line, theme_classic\n\ndf = tibble(x=numpy.linspace(0, 2 * pi, 500))\n(\n    df\n    >> mutate(y=sin(f.x), sign=if_else(f.y >= 0, "positive", "negative"))\n    >> ggplot(aes(x="x", y="y"))\n    + theme_classic()\n    + geom_line(aes(color="sign"), size=1.2)\n)\n```\n\n![example](./example.png)\n\n```python\n# very easy to integrate with other libraries\n# for example: klib\nimport klib\nfrom pipda import register_verb\nfrom datar import f\nfrom datar.data import iris\nfrom datar.dplyr import pull\n\ndist_plot = register_verb(func=klib.dist_plot)\niris >> pull(f.Sepal_Length) >> dist_plot()\n```\n\n![example](./example2.png)\n\n## Testimonials\n\n[@coforfe](https://github.com/coforfe):\n> Thanks for your excellent package to port R (`dplyr`) flow of processing to Python. I have been using other alternatives, and yours is the one that offers the most extensive and equivalent to what is possible now with `dplyr`.\n\n[1]: https://github.com/pwwang/datar-numpy\n[2]: https://github.com/pwwang/datar-pandas\n[3]: https://img.shields.io/codacy/coverage/0a7519dad44246b6bab30576895f6766?style=flat-square\n[4]: https://img.shields.io/codacy/coverage/45f4ea84ae024f1a8cf84be54dd144f7?style=flat-square\n[5]: https://pwwang.github.io/datar/\n[6]: https://img.shields.io/pypi/v/datar?style=flat-square\n[7]: https://pypi.org/project/datar/\n[8]: https://img.shields.io/github/v/tag/pwwang/datar?style=flat-square\n[9]: https://github.com/pwwang/datar\n[10]: https://img.shields.io/github/actions/workflow/status/pwwang/datar/ci.yml?branch=master&style=flat-square\n[11]: https://img.shields.io/github/actions/workflow/status/pwwang/datar/docs.yml?branch=master&style=flat-square\n[12]: https://img.shields.io/codacy/grade/3d9bdff4d7a34bdfb9cd9e254184cb35?style=flat-square\n[13]: https://app.codacy.com/gh/pwwang/datar\n[14]: https://img.shields.io/codacy/coverage/3d9bdff4d7a34bdfb9cd9e254184cb35?style=flat-square\n[15]: https://pwwang.github.io/datar/reference-maps/ALL/\n[16]: https://pwwang.github.io/datar/notebooks/across/\n[17]: https://pwwang.github.io/datar/api/datar/\n[18]: https://img.shields.io/pypi/v/datar-numpy?style=flat-square\n[19]: https://img.shields.io/pypi/v/datar-pandas?style=flat-square\n[20]: https://img.shields.io/pypi/dm/datar?style=flat-square\n[21]: https://github.com/tidyverse/dplyr\n[22]: https://github.com/pwwang/datar-arrow\n[23]: https://img.shields.io/codacy/coverage/5f4ef9dd2503437db18786ff9e841d8b?style=flat-square\n[24]: https://img.shields.io/pypi/v/datar-arrow?style=flat-square\n',
    'author': 'pwwang',
    'author_email': 'pwwang@pwwang.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/pwwang/datar',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
