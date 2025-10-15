#!/usr/bin/env python
import os
import sys
from codecs import open

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


# CURRENT_PYTHON = sys.version_info[:2]
# REQUIRED_PYTHON = (3, 7)

# if CURRENT_PYTHON < REQUIRED_PYTHON:
#     sys.stderr.write("""
# ==========================
# Unsupported Python version
# ==========================
# This version of arthub_api requires at least Python {}.{}, but
# you're trying to install it on Python {}.{}. To resolve this,
# consider upgrading to a supported Python version.
# """.format(*(REQUIRED_PYTHON + CURRENT_PYTHON)))
#     sys.exit(1)


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        try:
            from multiprocessing import cpu_count

            self.pytest_args = ["-n", str(cpu_count()), "--boxed"]
        except (ImportError, NotImplementedError):
            self.pytest_args = ["-n", "1", "--boxed"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


# 'setup.py publish' shortcut.
if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    sys.exit()

requires = [
    'requests>=2.25.1',
    'platformdirs==2.0.2',
    'tenacity==5.0.*; python_version < "3"',
    'tenacity>=8; python_version >= "3"',
    'six==1.16.*',
    'pycryptodome==3.16.0'
]

test_requirements = [
    "pytest",
]

about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "arthub_api", "__version__.py"), "r",
          "utf-8") as f:
    exec(f.read(), about)

with open("README.md", "r", "utf-8") as f:
    readme = f.read()

setup(name=about["__title__"],
      version=about["__version__"],
      description=about["__description__"],
      long_description=readme,
      long_description_content_type="text/markdown",
      author=about["__author__"],
      author_email=about["__author_email__"],
      url=about["__url__"],
      package_dir={'arthub_api': 'arthub_api'},
      packages=['arthub_api'],
      package_data={"": ["LICENSE", "NOTICE"]},
      include_package_data=True,
      install_requires=requires,
      license=about["__license__"],
      zip_safe=False,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Operating System :: OS Independent"],
      cmdclass={"test": PyTest},
      tests_require=test_requirements,
      entry_points={
          "console_scripts": [
              "aha = arthub_api.__main__:main",
          ]
      },
      extras_require={
        ':python_version == "2.7"': ['futures']
    })
