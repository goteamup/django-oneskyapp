#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="django-oneskyapp",
    version='0.1.6',
    url='http://github.com/pista329/django-oneskyapp',
    author='Stefan Backor',
    author_email='stefan@backor.sk',
    description='OneSkyApp translation service management commands '
                'for your django app',
    packages=find_packages(exclude='testapp'),
    install_requires=[
        'django>=1.4',
        'polib>=1.0',
        'requests>=2.0'
    ],
    license='MIT',
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ]
)
