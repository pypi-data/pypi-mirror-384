from __future__ import annotations

import importlib.util
import os
import platform
import re
import subprocess
import sys
from distutils.command.build_ext import build_ext
from pathlib import Path

from setuptools import Extension

is_windows = platform.system() == "Windows"


class CMakeExtension(Extension):
    def __init__(
        self,
        name: str,
        sources,
        cmake_project: os.PathLike,
        cmake_targets: list[str],
        *args,
        **kw,
    ):
        super().__init__(name, sources, *args, **kw)
        self.cmake_options = {
            "dir": os.fspath(Path(cmake_project).resolve()),
            "targets": cmake_targets,
        }


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.run(["cmake", "--version"], stdout=subprocess.PIPE, check=True, text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        self.cmake_version = tuple(int(d) for d in re.search(r"version\s*([\d.]+)", out.stdout).group(1).split("."))

        if is_windows:
            if self.cmake_version < (3, 1, 0):
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        super().run()

    def build_extension(self, ext):
        cmake_options = ext.cmake_options
        extdir = Path(self.get_ext_fullpath(ext.name)).parent.resolve()
        cmake_args = [
            f"-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DPYTHON_VERSION={sys.version_info.major}.{sys.version_info.minor}",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=YES",
        ]
        library_output_dir = extdir

        cfg = "Debug" if self.debug else "Release"
        build_args = ["--config", cfg]

        if self.cmake_version > (3, 12, 0):
            build_args.append("--parallel")

        if self.verbose:
            build_args.append("--verbose")

        if is_windows:
            cmake_args += [f"-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"]
            if sys.maxsize > 2**32:
                cmake_args += ["-A", "x64"]
            build_args += ["--", "/m", "/verbosity:minimal"]
            library_name_format = "{}.lib"
        else:
            cmake_args += ["-DCMAKE_BUILD_TYPE=" + cfg]
            library_name_format = "lib{}.a"

        env = os.environ.copy()
        env["CXXFLAGS"] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get("CXXFLAGS", ""), self.distribution.get_version())
        Path(self.build_temp).mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["cmake", cmake_options["dir"]] + cmake_args,
            cwd=self.build_temp,
            env=env,
            check=True,
        )
        if self.force:
            subprocess.run(
                ["cmake", "--build", ".", "--target", "clean"] + build_args,
                cwd=self.build_temp,
                check=True,
            )

        for target in cmake_options["targets"]:
            if self.verbose:
                print(["cmake", "--build", ".", "--target", target] + build_args)
            subprocess.run(
                ["cmake", "--build", ".", "--target", target] + build_args,
                cwd=self.build_temp,
                check=True,
            )

            ext.extra_objects.append(os.fspath(library_output_dir.joinpath(library_name_format.format(target))))

        super().build_extension(ext)


if importlib.util.find_spec("Cython") is not None:
    from Cython.Build import cythonize
    from Cython.Build.Dependencies import default_create_extension

    def cythonize_extensions(ext_modules: list[CMakeExtension], include_paths: list[str], compiler_directives: dict):
        def create_extension(template, kwds):
            """"""
            kwds["cmake_project"] = template.cmake_options["dir"]
            kwds["cmake_targets"] = template.cmake_options["targets"]
            return default_create_extension(template, kwds)

        cythonized_ext_modules = cythonize(
            ext_modules,
            include_path=include_paths,
            compiler_directives=compiler_directives,
            create_extension=create_extension,
        )

        for ext_module in cythonized_ext_modules:
            ext_module.include_dirs = include_paths

        return cythonized_ext_modules
