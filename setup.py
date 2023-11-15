#!/usr/bin/env python
import os
import re
import subprocess
import sys
from distutils.version import LooseVersion
import platform

from setuptools import setup
import warnings

from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

here = os.path.abspath(os.path.dirname(__file__))


def read_requirements_macos():
    with open('requirements.txt') as fp:
        return [row.strip() for row in fp if row.strip()]

if platform.system() == "Darwin":
    about = {}
    with open(os.path.join(here, 'mapilio_kit', 'components', 'version.py'), 'r') as f:
        exec(f.read(), about)

    setup(name='mapilio-kit',
          version=about['VERSION'],
          description='MAPILIO Image/Video Upload Pipeline',
          long_description=open('README.md').read(),
          long_description_content_type='text/markdown',
          url='https://github.com/mapilio/mapilio-kit-v2',
          author='Mapilio',
          license='MIT License',
          python_requires=">=3.6, !=3.12.*",
          packages=['mapilio_kit', 'mapilio_kit.base', 'mapilio_kit.components'],
          entry_points='''
          [console_scripts]
          mapilio_kit=mapilio_kit.__main__:main
          ''',
          install_requires=read_requirements_macos(),

          )
    print("Installed")


class MakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class MakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['make', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        cmake_version = LooseVersion(re.search(r'GNU Make\s*([\d.]+)', out.decode()).group(1))
        if cmake_version < LooseVersion('4.2.1'):
            raise RuntimeError("GNU Make >= 4.2.1 is required")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        export_path = os.path.join('mapilio_kit', 'base', 'bin')
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        subprocess.run(['make',
                        '-C',
                        os.path.join('extras', os.path.basename(ext.name)),
                        '-j'
                        ]
                       )
        subprocess.run(['cp', os.path.join('extras', 'max2sphere-batch/MAX2spherebatch'),
                        export_path])


def install_maxextractor():
    subprocess.run(['bash', 'max_extractor_install.sh'])


def read_requirements():
    install_maxextractor()
    with open('requirements.txt') as fp:
        return [row.strip() for row in fp if row.strip()]


def win_read_requirements():
    with open('requirements.txt') as fp:
        return [row.strip() for row in fp if row.strip()]


about = {}
with open(os.path.join(here, 'mapilio_kit','components', 'version.py'), 'r') as f:
    exec(f.read(), about)

if os.name == 'nt' or 'darwin':
    requires = win_read_requirements()
    ext_modules = []
    cmdclass = {}
else:
    requires = read_requirements()
    ext_modules = [MakeExtension('extras/max2sphere-batch')]
    cmdclass = dict(build_ext=MakeBuild)

setup(name='mapilio-kit',
      version=about['VERSION'],
      description='MAPILIO Image/Video Upload and Pipeline',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      url='https://github.com/mapilio/mapilio-kit-v2',
      author='Mapilio',
      license='MIT License',
      python_requires=">=3.6, !=3.12.*",
      ext_modules=ext_modules,
      cmdclass=cmdclass,
      packages=['mapilio_kit', 'mapilio_kit.base', 'mapilio_kit.components'],
      entry_points='''
      [console_scripts]
      mapilio_kit=mapilio_kit.__main__:main
      ''',
      install_requires=requires
      )
