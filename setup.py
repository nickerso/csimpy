from os import path
import re
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = f.read().splitlines()

def get_version(this_directory):
    with open(path.join(this_directory, 'csimpy/_version.py'), encoding='utf-8') as f:
        version_file = f.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='csimpy',
    version=get_version(this_directory),
    packages=['csimpy'],
    url='https://github.com/nickerso/csimpy',
    license='Apache 2.0',
    author='David Nickerson',
    author_email='d.nickerson@auckland.ac.nz',
    description='Using the BioSimulators-utils methods for handling SED-ML with CellML 2.0 models using libCellML.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'csimpy=csimpy.cli:main'
        ]
    },
    install_requires=requirements
)