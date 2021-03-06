from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    name = "ssfcommon",
    version = "0.1",
    author = "Ganesh Katrapati",
    author_email = "ganesh.katrapati@research.iiit.ac.in",
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("ssfc", ["__init__.pyx"])]
)
