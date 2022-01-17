from os import path
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='CSimPy',
    version='0.0.2a',
    py_modules=['csimpy'],
    package_dir={'': 'csimpy'},
    url='https://github.com/nickerso/csimpy',
    license='Apache 2.0',
    author='David Nickerson',
    author_email='d.nickerson@auckland.ac.nz',
    description='Using the BioSimulators-utils methods for handling SED-ML with CellML 2.0 models using libCellML.',
    long_description=long_description,
    long_description_content_type='text/markdown'
)