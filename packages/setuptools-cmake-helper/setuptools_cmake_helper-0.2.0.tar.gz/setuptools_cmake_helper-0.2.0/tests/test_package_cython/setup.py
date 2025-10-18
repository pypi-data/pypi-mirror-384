from __future__ import annotations

import os
from pathlib import Path

from setuptools import setup

import setuptools_cmake_helper

file_dir = Path(__file__).parent.absolute().relative_to(Path().absolute())

cmake_project_dir = file_dir.joinpath("cmake_src")

ext_modules = [
    setuptools_cmake_helper.CMakeExtension(
        "test_package._native",
        [
            os.fspath(file_dir.joinpath("wrap_src", "_native.pyx")),
        ],
        cmake_project=cmake_project_dir,
        cmake_targets=["native_test"],
        language="c",
        extra_compile_args=[],
        extra_objects=[],
        include_dirs=[os.fspath(cmake_project_dir)],
    )
]

cythonized_ext_modules = setuptools_cmake_helper.cythonize_extensions(
    ext_modules,
    include_paths=[os.fspath(cmake_project_dir)],
    compiler_directives={
        "embedsignature": True,
        "language_level": "3",
        "freethreading_compatible": True,
    },
)

setup(
    cmdclass={
        "build_ext": setuptools_cmake_helper.CMakeBuild,
    },
    ext_modules=cythonized_ext_modules,
)
