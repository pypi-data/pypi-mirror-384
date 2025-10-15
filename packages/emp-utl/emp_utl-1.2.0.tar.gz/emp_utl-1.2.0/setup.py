# Building setup to package 'emp_utl'
from setuptools import setup, find_packages

# Reading CHANGELOG.md as changelog
with open(file = 'CHANGELOG.md', mode = 'r', encoding = 'utf-8') as c:
    changelog = c.read()

# Reading README.md as base description
with open(file = 'src/README.md', mode = 'r', encoding = 'utf-8') as fh:
    readme = fh.read()

# Reading requirements.txt
with open(file = 'src/requirements.txt', mode = 'r', encoding = 'utf-8') as f:
    required = f.read().splitlines()

# Merge README and CHANGELOG for PyPI page
long_description = f'{readme}\n\n{changelog}'

# Setup
setup(
    name = 'emp_utl',
    version = '1.2.0',
    description = 'Customized modules for reusability in Project Enterprise Management Program (EMP)',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = 'AbdoCherry',
    packages = find_packages(where = 'src', include = ['emp_utl*']),
    package_dir = {'': 'src'},
    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires = required,
    license = 'MIT',
    url = 'https://github.com/AbdoCherry/EMP_UTL-S',
    python_requires = '>=3.8',
)