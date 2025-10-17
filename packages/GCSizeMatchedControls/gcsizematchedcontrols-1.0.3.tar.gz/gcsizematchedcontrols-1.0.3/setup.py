from setuptools import setup
from setuptools import find_packages

version_py = "GCSizeMatchedControls/_version.py"
exec(open(version_py).read())

setup(
    name="GCSizeMatchedControls", # Replace with your own username
    version=__version__,
    author="Benxia Hu",
    author_email="hubenxia@gmail.com",
    description="randomly select control genomic regions",
    long_description="randomly select size and GC-content matched genomic regions",
    url="https://pypi.org/project/GCSizeMatchedControls/",
    entry_points = {
        "console_scripts": ['GCSizeMatchedControls = GCSizeMatchedControls.GCSizeMatchedControls:main',]
        },
    python_requires = '>=3.12',
    packages = ['GCSizeMatchedControls'],
    install_requires = [
        'numpy',
        'pandas',
        'argparse',
        'pybedtools',
        'pysam',
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    zip_safe = False,
  )
