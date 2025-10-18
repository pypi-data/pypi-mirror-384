from __future__ import annotations

from pathlib import Path

import build

this_path = Path(__file__).parent


def test_simple(tmp_path):
    builder = build.ProjectBuilder(this_path.joinpath("test_package_simple_cpp"))
    builder.build("wheel", tmp_path)


def test_cython(tmp_path):
    builder = build.ProjectBuilder(this_path.joinpath("test_package_cython"))
    builder.build("wheel", tmp_path)
