import platform
import sys

from setuptools import Extension, find_packages, setup

if platform.system() == "Windows":
    extra_compile_args = ["/std:c++latest"]
else:
    extra_compile_args = ["-std=c++23"]

# only use the limited API if Python 3.11 or newer is used
# 3.11 added PyBuffer support to the limited API,
py_limited_api = sys.version_info >= (3, 11)
default_sources = [
    "src/EndianedBinaryIO/PyFloat_Half.cpp",
]
default_depends = [
    "src/EndianedBinaryIO/EndianedIOBase.hpp",
    "src/EndianedBinaryIO/PyConverter.hpp",
    "src/EndianedBinaryIO/PyFloat_Half.hpp",
]

setup(
    name="bier",
    packages=find_packages(),
    ext_modules=[
        Extension(
            "bier.EndianedBinaryIO.C.EndianedBytesIO",
            ["src/EndianedBinaryIO/EndianedBytesIO.cpp", *default_sources],
            depends=default_depends,
            language="c++",
            include_dirs=["src"],
            extra_compile_args=extra_compile_args,
            py_limited_api=py_limited_api,
        ),
        Extension(
            "bier.EndianedBinaryIO.C.EndianedStreamIO",
            ["src/EndianedBinaryIO/EndianedStreamIO.cpp", *default_sources],
            depends=default_depends,
            language="c++",
            include_dirs=["src"],
            extra_compile_args=extra_compile_args,
            py_limited_api=py_limited_api,
        ),
        # somehow slower than the pure python version
        # Extension(
        #     "bier.EndianedBinaryIO.C.EndianedIOBase",
        #     ["src/EndianedBinaryIO/EndianedIOBase.cpp"],
        #     depends=["src/PyConverter.hpp"],
        #     language="c++",
        #     include_dirs=["src"],
        #     extra_compile_args=["-std=c++23"],
        # ),
    ],
)
