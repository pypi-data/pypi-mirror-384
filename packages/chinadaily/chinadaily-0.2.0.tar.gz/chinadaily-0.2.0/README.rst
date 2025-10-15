=================
ChinaDailyProject
=================


.. image:: https://img.shields.io/pypi/v/chinadailyproject.svg
        :target: https://pypi.python.org/pypi/chinadailyproject

.. image:: https://img.shields.io/travis/yarving/chinadailyproject.svg
        :target: https://travis-ci.com/yarving/chinadailyproject

.. image:: https://readthedocs.org/projects/chinadailyproject/badge/?version=latest
        :target: https://chinadailyproject.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Download China Daily newspaper PDF


* Free software: GNU General Public License v3
* Documentation: https://chinadailyproject.readthedocs.io.


Installation and Upgrade
------------------------
* Installation: `pip install chinadaily`
* Upgrade: `pip install --upgrade chinadaily`

Usage
--------
* Download today's China Daily newspaper: `chinadaily`
* Download specific date's newspaper (eg 2020-10-10): `chinadaily 20201010`

How to Development
------------------
after development, do the following steps:

1. run test: `python setup.py test`
2. install a local development version: `python setup develop`
3. release a new version: `python setup.py sdist upload`

Features
--------

* 自动下载人民日报指定日期的PDF文件
* 支持下载当天、指定日期、整月或整年的报纸
* 智能识别并下载所有版面（多节点页面）的PDF链接
* 按正确顺序合并所有PDF文件
* 自动处理URL规范化和去重
* 详细的日志记录和错误处理
* 支持强制重新下载功能

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
