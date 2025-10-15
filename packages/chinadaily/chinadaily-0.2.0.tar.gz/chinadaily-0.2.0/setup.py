#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests==2.24.0',
    'PyPDF2==1.26.0',
    'beautifulsoup4==4.9.3',
    'lxml==4.6.1',
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="ChinaDaily",
    author_email='yarving@qq.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Download China Daily newspaper PDF",
    entry_points={
        'console_scripts': [
            'chinadaily=chinadaily.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='chinadaily',
    name='chinadaily',
    packages=find_packages(include=['chinadaily', 'chinadaily.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/yarving/chinadailyproject',
    version='0.2.0',
    zip_safe=False,
)
