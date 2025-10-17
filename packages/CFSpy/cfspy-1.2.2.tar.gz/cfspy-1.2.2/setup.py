
from setuptools import setup, find_packages
import codecs
import os

VERSION = '1.2.2'
DESCRIPTION = 'Chen-Fliess series computation'

with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Setting up
setup(
    name="CFSpy",
    version=VERSION,
    author="Ivan Perez Avellaneda",
    author_email="<iperezave@gmail.com>",
    license="MIT",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/iperezav/CFSpy/',
    packages=find_packages(),
    install_requires=['numpy', 'sympy'],
    keywords=['Chen-Fliess series', 'nonlinear system', 'input-output system', 'ODEs', 'control system', 'system theory', 'python'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
