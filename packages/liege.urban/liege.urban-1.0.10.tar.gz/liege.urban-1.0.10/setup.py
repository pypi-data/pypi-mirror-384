# -*- coding: utf-8 -*-
"""Installer for the liege.urban package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read() +
    '\n' +
    'Contributors\n' +
    '============\n' +
    '\n' +
    open('CONTRIBUTORS.rst').read() +
    '\n' +
    open('CHANGES.rst').read() +
    '\n')


setup(
    name='liege.urban',
    version='1.0.10',
    description="Liège urban profile",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone',
    author='Simon Delcourt',
    author_email='simon.delcourt@imio.be',
    url='https://pypi.python.org/pypi/liege.urban',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['liege'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'borg.localrole',
        'plone.api',
        'Products.urban',
        'imio.pm.wsclient',
        'setuptools',
        'zope.schema',
        'z3c.jbot',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.app.robotframework[debug]',
            'ipdb',
        ],
        'pytest': [
            'pytest',
            'gocept.pytestlayer',
        ],
    },
    entry_points={
        'z3c.autoinclude.plugin': ['target = plone'],
        'Products.urban.testing.profile': [
            'base = liege.urban.testing:override_testing_profile',
            'layers = liege.urban.testing:override_testing_layers',
        ],
    },
)
