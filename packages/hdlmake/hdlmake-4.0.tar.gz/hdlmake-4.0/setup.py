# Note: if pip is not installed, try to bootstrap using:
#   python -m ensurepip --default-pip
# Or download https://bootstrap.pypa.io/get-pip.py
#
# Then install setuptools:
# python -m pip install --upgrade pip setuptools wheel
from setuptools import (setup, find_packages)
from pathlib import Path

this_directory = Path(__file__).parent
exec(open(this_directory / "hdlmake" / "_version.py").read())
long_description = (this_directory / "README.md").read_text()

try:
    __version__
except Exception:
    __version__ = "0.0"  # default if for some reason the exec did not work

setup(
   name="hdlmake",
   version=__version__,
   description="Hdlmake generates multi-purpose makefiles for HDL projects management.",
   long_description=long_description,
   long_description_content_type='text/markdown',
   author="Javier D. Garcia-Lasheras, CERN",
   license="GPLv3",
   url="https://gitlab.com/ohwr/project/hdl-make",
   packages=find_packages(),
   entry_points={
      'console_scripts': [
         'hdlmake = hdlmake.main:main',
         ], 
   },
   include_package_data=True,  # use MANIFEST.in during install
   classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Topic :: Utilities",
      "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
      "Topic :: Software Development :: Build Tools",
    ],
   )
