from setuptools import setup, find_packages

from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='digimat.mbio',
    version='0.1.169',
    description='Digimat MBIO System',
    long_description=long_description,
    namespace_packages=['digimat'],
    author='Frederic Hess',
    author_email='fhess@st-sa.ch',
    url='https://github.com/digimat/digimat-mbio',
    license='PSF',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'digimat.lp',
        'digimat.units',
        'digimat.danfossally',
        'ptable',
        'rich',
        # https://github.com/pymodbus-dev/pymodbus/releases
        # Version 3.8.0 is yet problematic (async loop in subthread)
        # 3.7.4 isn't working
        # 3.7.3 is buggy but working
        # 3.7.2 is ok
        'pymodbus == 3.7.2',
        'requests',
        'httpx',
        # cryptography and netifaces setup problem
        # 'xknx',
        'openpyxl',
        'ipcalc',
        'gspread',
        'packaging',
        'setuptools'
    ],
    dependency_links=[
        ''
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
    ],
    zip_safe=False)
