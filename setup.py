#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Setup
"""

import sys
from setuptools import setup, find_packages


about = {}
with open('__about__.py') as fp:
    exec(fp.read(), about)

extras_require = {
    'tests' : [
        'pyyaml',
        'pytest',
        'pytest-cache',
        'pytest-cover',
        'pytest-flakes',
        'pytest-pycodestyle',
        'flake8',
    ]
}
    
classifiers = [
    'Development Status :: 6 - Mature',
    'Programming Language :: Python :: 3',
    'Natural Language :: English',
    'Topic :: Office/Business :: Financial :: Accounting',
    'Topic :: Utilities',
    'Environment :: Console',
    'Operating System :: OS Independent',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
]

kw = {
    'name': about['__package_name__'],
    'version': about['__version__'],
    'author': about['__author__'],
    'author_email': about['__email__'],
    'description': about['__description__'],
    'url': about['__url__'],
    'classifiers': classifiers,
    'license': about['__license__'],
    'keywords': ["ofx", "banking", "statement", "beancount",
                 "degiro", "ing", "icscards", "knab"],
    'packages': find_packages('src'),
    'package_dir': {'': 'src'},
    'namespace_packages': ["ofxstatement", "ofxstatement.plugins"],
    'include_package_data': True,
    'install_requires': ['ofxstatement>0.6.4'],
    'extras_require': extras_require,
    'setup_requires': [
        'setuptools>=39.1.0',
    ],
    'zip_safe': True,
    'entry_points': {
        'ofxstatement':
        ['nl-degiro = ofxstatement.plugins.nl.degiro:Plugin',
         'nl-icscards = ofxstatement.plugins.nl.icscards:Plugin',
         'nl-ing = ofxstatement.plugins.nl.ing:Plugin',
         'nl-knab = ofxstatement.plugins.nl.knab:Plugin',
         'nl-asn = ofxstatement.plugins.nl.asn:Plugin']
    },
}

if __name__ == '__main__':
    if sys.argv[-1] == 'info':
        for k, v in about.items():
            print('%s: %s' % (k, v))
        sys.exit()
    else:
        setup(**kw)
