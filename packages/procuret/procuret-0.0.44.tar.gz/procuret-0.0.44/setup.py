"""
Procuret API
PyPI Setup Module
author: hugh@blinkybeach.com
"""
from setuptools import setup, find_packages
from os import path
from codecs import open
from procuret.version import VERSION

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'readme.md'), encoding='utf-8') as readme_file:
    LONG_DESCRIPTION = readme_file.read()

setup(
    name='procuret',
    version=VERSION,
    description='Procuret API Library',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/procuret/procuret-python',
    author='Procuret',
    author_email='hugh@procuret.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Office/Business :: Financial'
    ],
    keywords='library http api web payments finance',
    packages=find_packages(),
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
    project_urls={
        'Github Repository': 'https://github.com/procuret/procuret-python',
        'About': 'https://github.com/procuret/procuret-python'
    }
)
