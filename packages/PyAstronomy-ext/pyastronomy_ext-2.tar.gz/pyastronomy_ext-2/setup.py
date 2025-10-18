# -*- coding: utf-8 -*-
from __future__ import print_function

whichSetup = "None"

try:
    from numpy.distutils.core import setup
    whichSetup = "numpy.distutils.core"
except ImportError:
    from setuptools import setup
    whichSetup = "setuptools"
except ImportError:
    from distutils.core import setup
    whichSetup = "distutils.core"

import sys
import re

from distutils.extension import Extension as old_Extension

cxx_ext_re = re.compile(r'.*[.](cpp|cxx|cc)\Z', re.I).match
fortran_pyf_ext_re = re.compile(
    r'.*[.](f90|f95|f77|for|ftn|f|pyf)\Z', re.I).match


class Extension(old_Extension):
    def __init__(self, name, sources,
                 include_dirs=None,
                 define_macros=None,
                 undef_macros=None,
                 library_dirs=None,
                 libraries=None,
                 runtime_library_dirs=None,
                 extra_objects=None,
                 extra_compile_args=None,
                 extra_link_args=None,
                 export_symbols=None,
                 swig_opts=None,
                 depends=None,
                 language=None,
                 f2py_options=None,
                 module_dirs=None,
                 optional=False
                 ):
        old_Extension.__init__(self, name, [],
                               include_dirs,
                               define_macros,
                               undef_macros,
                               library_dirs,
                               libraries,
                               runtime_library_dirs,
                               extra_objects,
                               extra_compile_args,
                               extra_link_args,
                               export_symbols)
        # Avoid assert statements checking that sources contains strings:
        self.sources = sources

        # Python 2.4 distutils new features
        self.swig_opts = swig_opts or []

        # Python 2.3 distutils new features
        self.depends = depends or []
        self.language = language

        # numpy_distutils features
        self.f2py_options = f2py_options or []
        self.module_dirs = module_dirs or []

        return

    def has_cxx_sources(self):
        for source in self.sources:
            if cxx_ext_re(str(source)):
                return True
        return False

    def has_f2py_sources(self):
        for source in self.sources:
            if fortran_pyf_ext_re(source):
                return True
        return False



# By default build public distribution
sdist = False

for s in sys.argv:
    if s == "sdist":
        sdist = True


# List of packages
packages = ['PyAstronomy_ext', 'PyAstronomy_ext.forTrans']


extOccultnl = Extension('PyAstronomy_ext.forTrans.occultnl',
                        sources=['PyAstronomy_ext/forTrans/occultnl.pyf',
                                 'PyAstronomy_ext/forTrans/occultnl.f'], optional=True)
extOccultquad = Extension('PyAstronomy_ext.forTrans.occultquad',
                          sources=['PyAstronomy_ext/forTrans/occultquad.pyf',
                                   'PyAstronomy_ext/forTrans/occultquad.f'], optional=True)

ext_modules = [extOccultnl, extOccultquad]



setup(name='PyAstronomy_ext',
      url="http://www.hs.uni-hamburg.de/DE/Ins/Per/Czesla/PyA/PyA/index.html",
      description='Optional extension for PyAstronomy.',
      version="2",
      packages=packages,
      ext_modules=ext_modules,
      package_dir={'PyAstronomy_ext': 'PyAstronomy_ext'},
      install_requires=['numpy', 'six'],
      # Do not forget to give the ``correct'' name for the module! (here, e.g., PyAstronomy.funcFit)
      author='PyA group',
      author_email='stefan.czesla@hs.uni-hamburg.de',
      )
