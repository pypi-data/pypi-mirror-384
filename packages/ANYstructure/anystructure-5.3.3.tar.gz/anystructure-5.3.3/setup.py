"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

def readme():
    with open('README.rst') as file:
        return file.read()

setup(
    name='ANYstructure',  # Required
    url = 'https://github.com/audunarn/ANYstructure',
    entry_points={"console_scripts": ['ANYstructure = anystruct.__main__:main']},
    version='5.3.3',  # Required
    license='MIT',
    description='A plate field optimization tool for offshore structures calculated according to DNV standards',
    long_description = readme(),
    author='Audun Arnesen Nyhus',  # Optional
    author_email='audunarn@gmail.com',  # Optional
    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering'],
    keywords='dnv-gl-os-c101 dnv-rp-c202 dnv-rp-c201 naval_architecture structural_engineering steel buckling fatigue local_scantlings optimization weight',
    include_package_data=True,
    install_requires=['scipy', 'numpy', 'matplotlib', 'reportlab', 'xlwings', 'scikit-learn'],
    packages=['anystruct'],
    py_modules = [],
)